"""
FastAPI Backend for Language Bridge and Content Moderation Service
Created by Claude
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import os
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
import json
from openai import OpenAI

# Load environment variables
load_dotenv()

# Import our agents
from Language_Bridge_Agent import process_with_moderation, translate_response_to_user_language, clean_formatting_for_translation
from grader import grade_assignment_from_blob, validate_pdf_blob
from explanation import EducationalAIAgent
from Quiz_Generation_Agent import create_quiz, get_quiz_requirements
from backend_cache import cache_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EdRoom Intelligent Language Bridge API",
    description="AI-powered API for translation, content moderation, grading, and educational explanations with intelligent intent classification",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:4173",  # Vite preview
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class TextProcessRequest(BaseModel):
    text: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

class TextProcessResponse(BaseModel):
    success: bool
    input_text: str
    original_language: str
    original_language_code: str
    translation_confidence: float
    translated_text: str
    is_english: bool
    moderation_approved: bool
    moderation_confidence: float
    flagged_categories: List[str]
    moderation_explanation: str
    final_approved: bool
    error: Optional[str]
    processing_time_ms: int
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    pdf_file: Optional[str] = None  # Base64 encoded PDF data

class ExplanationRequest(BaseModel):
    topic: str
    user_id: Optional[str] = "anonymous"
    include_history: Optional[bool] = True

class ExplanationResponse(BaseModel):
    success: bool
    topic: str
    explanation: str
    timestamp: str
    error: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    user_message: str
    bot_response: str
    translation_info: Optional[Dict[str, Any]] = None
    moderation_info: Optional[Dict[str, Any]] = None
    grading_result: Optional[Dict[str, Any]] = None
    explanation_result: Optional[Dict[str, Any]] = None
    final_approved: bool
    timestamp: str
    error: Optional[str] = None

class QuizGenerationRequest(BaseModel):
    topic: str
    difficulty: str
    user_id: Optional[str] = "anonymous"

class QuizGenerationResponse(BaseModel):
    success: bool
    quiz_info: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    details: Optional[List[str]] = None
    timestamp: str

# Global variables for service status
service_status = {
    "translation": "unknown",
    "moderation": "unknown",
    "explanation": "unknown",
    "startup_time": datetime.now().isoformat()
}

# Initialize Educational AI Agent and OpenAI client
explanation_agent = None
openai_client = None

# Intent classification function using ChatOpenAI
async def classify_user_intent(user_message: str) -> Dict[str, Any]:
    """
    Use ChatOpenAI to intelligently classify user intent for assessment or explanation
    
    Args:
        user_message (str): The user's message to classify
        
    Returns:
        Dict containing intent classification results
    """
    global openai_client
    
    if not openai_client:
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "reasoning": "OpenAI client not available"
        }
    
    try:
        system_prompt = """
You are an intelligent intent classifier for an educational platform. Analyze the user's message and determine their primary intent.

Classify the intent as one of these categories:
1. "grading" - User wants to grade, evaluate, assess, score, or get feedback on their work/assignment
2. "explanation" - User wants to learn about, understand, or get an explanation of a concept/topic
3. "general" - General conversation, greetings, or unclear intent

Consider context clues like:
- Grading: mentions of assignments, homework, tests, scores, evaluation, feedback, "how did I do", "grade this", "assess my work"
- Explanation: questions about concepts, "what is", "how does", "explain", "tell me about", learning requests
- General: greetings, casual conversation, unclear requests

Respond with a JSON object containing:
{
  "intent": "grading|explanation|general",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why you chose this intent"
}
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this message: '{user_message}'"}
            ],
            max_tokens=200,
            temperature=0.1,  # Low temperature for consistent classification
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate the response structure
        if "intent" not in result or "confidence" not in result:
            raise ValueError("Invalid response format from OpenAI")
            
        # Ensure confidence is between 0 and 1
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
        
        logger.info(f"Intent classified: {result['intent']} (confidence: {result['confidence']:.2f}) - {result.get('reasoning', '')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {
            "intent": "general",
            "confidence": 0.0,
            "reasoning": f"Classification failed: {str(e)}"
        }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global explanation_agent, openai_client
    logger.info("🚀 Starting Language Bridge & Content Moderation API...")
    
    # Check environment variables
    missing_vars = []
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
        service_status["translation"] = "missing_credentials"
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
        service_status["moderation"] = "missing_credentials"
        service_status["explanation"] = "missing_credentials"
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    
    # Initialize OpenAI client
    try:
        if os.getenv("OPENAI_API_KEY"):
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ OpenAI client initialized successfully!")
        else:
            logger.warning("⚠️ OpenAI API key not found - intent classification will be disabled")
    except Exception as e:
        logger.error(f"❌ OpenAI client initialization failed: {e}")
    
    # Initialize explanation agent
    try:
        explanation_agent = EducationalAIAgent()
        service_status["explanation"] = "healthy"
        logger.info("✅ Educational AI Agent initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Educational AI Agent initialization failed: {e}")
        service_status["explanation"] = "error"
    
    # Test services
    try:
        test_result = process_with_moderation("Hello, this is a test.")
        if test_result["success"]:
            service_status["translation"] = "healthy"
            service_status["moderation"] = "healthy"
            logger.info("✅ Translation and moderation services initialized successfully!")
        else:
            logger.error(f"❌ Service initialization failed: {test_result['error']}")
            if "translation" in test_result["error"].lower():
                service_status["translation"] = "error"
            if "moderation" in test_result["error"].lower():
                service_status["moderation"] = "error"
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")
        service_status["translation"] = "error"
        service_status["moderation"] = "error"

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "🌍🛡️🎓🤖 EdRoom Intelligent Language Bridge API",
        "description": "AI-powered backend with intelligent intent classification for translation, content moderation, grading, and educational explanations",
        "version": "2.0.0",
        "features": [
            "Multi-language translation",
            "Content moderation",
            "PDF grading with AI assessment",
            "Educational explanations",
            "Intelligent intent classification using ChatOpenAI",
            "User authentication"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "process": "/api/process",
            "chat": "/api/chat",
            "explain": "/api/explain",
            "status": "/api/status"
        },
        "frontend": {
            "note": "Frontend runs separately on React/Vite dev server",
            "typical_ports": ["http://localhost:3000", "http://localhost:5173"]
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if all(status in ["healthy", "unknown"] for status in service_status.values() if status != service_status["startup_time"]) else "degraded",
        timestamp=datetime.now().isoformat(),
        services={
            "translation": service_status["translation"],
            "moderation": service_status["moderation"],
            "explanation": service_status["explanation"],
            "startup_time": service_status["startup_time"]
        }
    )

@app.post("/api/process", response_model=TextProcessResponse)
async def process_text(request: TextProcessRequest):
    """
    Process text through translation and content moderation
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"📝 Processing request from user: {request.user_id}")
        
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text input is required and cannot be empty")
        
        if len(request.text) > 10000:
            raise HTTPException(status_code=400, detail="Text input is too long (maximum 10,000 characters)")
        
        # Process the text
        result = process_with_moderation(request.text)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if result["success"]:
            logger.info(f"✅ Processing completed successfully in {processing_time:.0f}ms")
            
            return TextProcessResponse(
                success=True,
                input_text=result["input_text"],
                original_language=result["original_language"],
                original_language_code=result["original_language_code"],
                translation_confidence=result["translation_confidence"],
                translated_text=result["translated_text"],
                is_english=result["is_english"],
                moderation_approved=result["moderation_approved"],
                moderation_confidence=result["moderation_confidence"],
                flagged_categories=result["flagged_categories"],
                moderation_explanation=result["moderation_explanation"],
                final_approved=result["final_approved"],
                error=None,
                processing_time_ms=int(processing_time),
                timestamp=datetime.now().isoformat()
            )
        else:
            logger.error(f"❌ Processing failed: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {result['error']}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """
    Intelligent chatbot endpoint with AI-powered intent classification for grading and educational explanations
    Enhanced with backend caching for improved offline resilience
    """
    try:
        logger.info(f"💬 Chat request from user: {request.user_id}")
        
        # Validate input - either message or PDF file must be provided
        if (not request.message or not request.message.strip()) and not request.pdf_file:
            return ChatResponse(
                success=False,
                user_message=request.message or "",
                bot_response="Please enter a message or upload a PDF file for me to process.",
                final_approved=False,
                timestamp=datetime.now().isoformat(),
                error="Empty input"
            )
        
        # Check cache first (only for text messages without PDF)
        cache_key_message = request.message or ""
        has_pdf = bool(request.pdf_file)
        
        if cache_key_message.strip() and not has_pdf:
            cached_response = cache_instance.get(cache_key_message, has_pdf=False)
            if cached_response:
                logger.info(f"✅ Cache hit for message: {cache_key_message[:50]}...")
                # Add cache annotation to response
                cached_bot_response = f"**[Cached Response]** {cached_response['bot_response']}"
                return ChatResponse(
                    success=cached_response.get('success', True),
                    user_message=cache_key_message,
                    bot_response=cached_bot_response,
                    translation_info=cached_response.get('translation_info'),
                    moderation_info=None,
                    grading_result=None,
                    explanation_result=cached_response.get('explanation_result'),
                    final_approved=cached_response.get('final_approved', True),
                    timestamp=datetime.now().isoformat()
                )
        
        # Initialize response components
        translation_info = None
        moderation_info = None
        grading_result = None
        explanation_result = None
        final_approved = True
        bot_response_parts = []
        original_language_code = None  # Store for response translation
        
        # Step 1: Process text message if provided (Translation + Moderation)
        should_grade_pdf = False
        if request.message and request.message.strip():
            logger.info("Step 1: Processing text message for translation and moderation...")
            result = process_with_moderation(request.message)
            
            if result["success"]:
                final_approved = result["final_approved"]
                
                # Store translation and moderation info
                if not result["is_english"]:
                    original_language_code = result["original_language_code"]  # Store for response translation
                    logger.info(f"Detected language: {result['original_language']} (code: {original_language_code})")
                    translation_info = {
                        "original_language": result["original_language"],
                        "translated_text": result["translated_text"],
                        "confidence": result["translation_confidence"]
                    }
                
                moderation_info = {
                    "approved": result["moderation_approved"],
                    "confidence": result["moderation_confidence"],
                    "flagged_categories": result["flagged_categories"],
                    "explanation": result["moderation_explanation"]
                }
                
                # Step 2: Use ChatOpenAI to intelligently classify user intent
                logger.info("Step 2: Classifying user intent with ChatOpenAI...")
                intent_result = await classify_user_intent(result["translated_text"])
                
                should_grade_pdf = intent_result["intent"] == "grading" and intent_result["confidence"] > 0.5
                should_explain = intent_result["intent"] == "explanation" and intent_result["confidence"] > 0.5
                
                # Log the intent classification for debugging
                logger.info(f"Intent classification: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f}) - {intent_result.get('reasoning', '')}")
                
                # Generate clean, user-friendly response
                if result["final_approved"]:
                    if not result["is_english"]:
                        # Only show translation if it's not English
                        bot_response_parts.append(f"🌐 **Translated from {result['original_language']}:** {result['translated_text']}")
                    else:
                        # For English messages, add a simple acknowledgment
                        bot_response_parts.append("💬 **Message received and processed.**")
                    
                    # Add clean intent-based responses
                    if should_grade_pdf and request.pdf_file:
                        bot_response_parts.append("📝 **Processing your document for grading...**")
                    elif should_grade_pdf and not request.pdf_file:
                        bot_response_parts.append("📄 **Please upload a PDF file to grade.**")
                    elif intent_result["intent"] == "grading" and intent_result["confidence"] <= 0.5:
                        bot_response_parts.append("🤔 **Want me to grade something?** Please upload a PDF file and be more specific.")
                    
                    # Add clean explanation functionality
                    if should_explain and explanation_agent and service_status["explanation"] == "healthy":
                        logger.info(f"Step 2.5: Processing explanation request (confidence: {intent_result['confidence']:.2f})...")
                        try:
                            explanation_text = explanation_agent.get_explanation(result["translated_text"])
                            
                            # Translate explanation back to user's language if needed (cleaning handled in translate function)
                            if original_language_code:
                                try:
                                    explanation_translation = translate_response_to_user_language(
                                        response_text=explanation_text,  # Don't pre-clean here, let translate function handle it
                                        target_language_code=original_language_code
                                    )
                                    if explanation_translation.get("success") and not explanation_translation.get("skipped"):
                                        explanation_text = explanation_translation["translated_text"]
                                        logger.info(f"✅ Explanation translated to user's language")
                                except Exception as e:
                                    logger.warning(f"Failed to translate explanation: {e}")
                            
                            explanation_result = {
                                "topic": result["translated_text"],
                                "explanation": explanation_text,
                                "intent_confidence": intent_result["confidence"],
                                "reasoning": intent_result.get("reasoning", "")
                            }
                            bot_response_parts.append(f"🎓 **Here's what I can tell you about {result['translated_text']}:**\n\n{explanation_text}")
                        except Exception as e:
                            logger.error(f"Explanation generation error: {e}")
                            bot_response_parts.append("❌ **Sorry, I couldn't generate an explanation right now. Please try again.**")
                    elif should_explain and (not explanation_agent or service_status["explanation"] != "healthy"):
                        bot_response_parts.append("❌ **Sorry, the explanation service is currently unavailable.**")
                    elif intent_result["intent"] == "explanation" and intent_result["confidence"] <= 0.5:
                        bot_response_parts.append("🤔 **Want me to explain something?** Please be more specific about the topic.")
                    elif intent_result["intent"] == "general":
                        bot_response_parts.append("💬 **Thanks for your message!** How can I help you today?")
                    
                    # Ensure we always have a response for non-English users
                    if not result["is_english"] and len([part for part in bot_response_parts if not part.startswith("🌐")]) == 0:
                        bot_response_parts.append("💬 **Thank you for your message. I understand what you're saying.**")
                        
                else:
                    bot_response_parts.append("❌ **Sorry, I can't process this message as it doesn't meet our content guidelines. Please try rephrasing your request.**")
                    # Don't proceed with grading or explanation if content is not approved
                    should_grade_pdf = False
                    should_explain = False
            else:
                logger.error(f"Translation/moderation failed: {result}")
                bot_response_parts.append("❌ **Sorry, I encountered an issue processing your message. Please try again.**")
                should_grade_pdf = False
        
        # Step 3: Process PDF file if provided AND grading is requested/appropriate
        if request.pdf_file:
            # If no text message provided, assume grading is requested
            if not request.message or not request.message.strip():
                should_grade_pdf = True
                bot_response_parts.append("📄 **PDF file received** - Processing for grading...")
            
            if should_grade_pdf:
                logger.info("Step 2: Processing PDF file for grading...")
                try:
                    # Validate PDF
                    if not validate_pdf_blob(request.pdf_file):
                        bot_response_parts.append("❌ **Invalid PDF file.** Please upload a valid PDF document.")
                    else:
                        # Create custom rubric based on user's message if available
                        if request.message and request.message.strip() and translation_info:
                            # Use translated text to create contextual rubric
                            user_context = translation_info["translated_text"] if translation_info else request.message
                            custom_rubric = f"""
                            Based on the user's request: "{user_context}"
                            
                            Grading Criteria:
                            - Content Quality and Relevance (40 marks)
                            - Clarity and Understanding (25 marks)
                            - Organization and Structure (20 marks)
                            - Grammar and Presentation (15 marks)
                            
                            Instructions:
                            - Provide specific feedback related to the user's request
                            - Ignore minor syntax/grammar mistakes
                            - Focus on content accuracy and comprehension
                            - Give constructive suggestions for improvement
                            """
                        else:
                            # Default rubric
                            custom_rubric = """
                            General Assignment Grading Criteria:
                            - Content Quality and Accuracy (40 marks)
                            - Clarity of Explanation (30 marks)
                            - Organization and Structure (20 marks)
                            - Grammar and Presentation (10 marks)
                            
                            Instructions:
                            - Ignore minor syntax/grammar mistakes
                            - Provide constructive feedback
                            - Focus on overall understanding and presentation
                            """
                        
                        # Grade the PDF
                        logger.info("Grading PDF with AI...")
                        pdf_result = grade_assignment_from_blob(request.pdf_file, custom_rubric, total_marks=100)
                        
                        grading_result = {
                            "marks_obtained": pdf_result["marks_obtained"],
                            "total_marks": pdf_result["total_marks"],
                            "ai_feedback": pdf_result["ai_feedback"]
                        }
                        
                        # Generate PDF response with enhanced feedback
                        percentage = (pdf_result["marks_obtained"] / pdf_result["total_marks"]) * 100
                        
                        if percentage >= 90:
                            grade_emoji = "🏆"
                            grade_level = "Excellent"
                        elif percentage >= 80:
                            grade_emoji = "🎉"
                            grade_level = "Very Good"
                        elif percentage >= 70:
                            grade_emoji = "✅"
                            grade_level = "Good"
                        elif percentage >= 60:
                            grade_emoji = "👍"
                            grade_level = "Satisfactory"
                        elif percentage >= 50:
                            grade_emoji = "⚠️"
                            grade_level = "Needs Improvement"
                        else:
                            grade_emoji = "❌"
                            grade_level = "Unsatisfactory"
                        
                        bot_response_parts.append(f"{grade_emoji} **Your Grade: {pdf_result['marks_obtained']}/{pdf_result['total_marks']} ({percentage:.1f}%)**\n\n🏅 **Performance:** {grade_level}\n\n📝 **Feedback:**\n{pdf_result['ai_feedback']}")
                        
                except Exception as pdf_error:
                    logger.error(f"PDF processing error: {pdf_error}")
                    bot_response_parts.append("❌ **Sorry, I couldn't process your PDF file. Please make sure it's a valid document and try again.**")
            else:
                bot_response_parts.append("📄 **I see you've uploaded a PDF file.** If you'd like me to grade it, just ask me to evaluate or assess your work!")
        
        # Debug: Log response parts before combining
        logger.info(f"Bot response parts count: {len(bot_response_parts)}")
        for i, part in enumerate(bot_response_parts):
            logger.info(f"Response part {i}: {part[:100]}{'...' if len(part) > 100 else ''}")
        
        # Combine all response parts
        if len(bot_response_parts) > 1:
            final_bot_response = "\n\n".join(bot_response_parts)
        elif len(bot_response_parts) == 1:
            final_bot_response = bot_response_parts[0]
        else:
            final_bot_response = "✅ Processing completed!"
        
        logger.info(f"Final bot response before translation: {final_bot_response[:200]}{'...' if len(final_bot_response) > 200 else ''}")
        
        # Translate response back to user's original language if needed
        if translation_info and translation_info.get("original_language") != "English":
            logger.info(f"Translating response back to user's language: {translation_info.get('original_language')}")
            try:
                # Use the stored original language code
                if original_language_code:
                    logger.info(f"Attempting to translate response to language code: {original_language_code}")
                    response_translation = translate_response_to_user_language(
                        response_text=final_bot_response,
                        target_language_code=original_language_code
                    )
                    
                    logger.info(f"Translation result: {response_translation}")
                    
                    if response_translation.get("success") and not response_translation.get("skipped"):
                        final_bot_response = response_translation["translated_text"]
                        logger.info(f"✅ Response translated back to {translation_info.get('original_language')}")
                        logger.info(f"Translated response preview: {final_bot_response[:100]}...")
                        logger.info(f"Final response length: {len(final_bot_response)} characters")
                    else:
                        logger.error(f"Failed to translate response back to user's language: {response_translation.get('error', 'Unknown error')}")
                        logger.error(f"Full translation response: {response_translation}")
                        logger.warning("Using original English response as fallback")
                else:
                    logger.warning(f"No original language code available for translation")
                    
            except Exception as e:
                logger.error(f"Error translating response to user's language: {e}")
                logger.warning("Using original English response as fallback")
        
        # Final debug log
        logger.info(f"Sending final response with length: {len(final_bot_response)} characters")
        logger.info(f"Final response starts with: {final_bot_response[:50]}...")
        
        # Prepare response data
        response_data = {
            'success': True,
            'bot_response': final_bot_response,
            'translation_info': translation_info,
            'explanation_result': explanation_result,
            'final_approved': final_approved
        }
        
        # Cache successful response (only for text messages without PDF)
        if cache_key_message.strip() and not has_pdf and final_approved:
            try:
                cache_instance.put(cache_key_message, response_data, has_pdf=False)
                logger.debug(f"✅ Response cached for: {cache_key_message[:50]}...")
            except Exception as cache_error:
                logger.warning(f"Failed to cache response: {cache_error}")
        
        return ChatResponse(
            success=True,
            user_message=request.message or "PDF file uploaded",
            bot_response=final_bot_response,
            translation_info=translation_info,
            moderation_info=moderation_info,
            grading_result=grading_result,
            explanation_result=explanation_result,
            final_approved=final_approved,
            timestamp=datetime.now().isoformat()
        )
            
    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {e}")
        
        # Try to provide a cached or fallback response on error
        fallback_message = request.message or "PDF file uploaded"
        try:
            if fallback_message.strip() and not has_pdf:
                # Try cache first
                cached_response = cache_instance.get(fallback_message, has_pdf=False)
                if cached_response:
                    logger.info(f"🔄 Using cached response as fallback for error")
                    fallback_bot_response = f"**[Cached Fallback]** Service temporarily unavailable. Here's a previous response:\n\n{cached_response['bot_response']}"
                    return ChatResponse(
                        success=True,
                        user_message=fallback_message,
                        bot_response=fallback_bot_response,
                        translation_info=cached_response.get('translation_info'),
                        moderation_info=None,
                        grading_result=None,
                        explanation_result=cached_response.get('explanation_result'),
                        final_approved=cached_response.get('final_approved', True),
                        timestamp=datetime.now().isoformat()
                    )
                
                # Generate structured fallback response
                fallback_response = cache_instance.get_fallback_response(fallback_message, "service_error")
                logger.info(f"🔄 Using structured fallback response")
                return ChatResponse(
                    success=True,
                    user_message=fallback_message,
                    bot_response=fallback_response['bot_response'],
                    translation_info=None,
                    moderation_info=None,
                    grading_result=None,
                    explanation_result=None,
                    final_approved=True,
                    timestamp=datetime.now().isoformat()
                )
        except Exception as fallback_error:
            logger.error(f"Fallback response generation failed: {fallback_error}")
        
        # Last resort error response
        return ChatResponse(
            success=False,
            user_message=fallback_message,
            bot_response="Sorry, I'm experiencing technical difficulties. Please try again later.",
            final_approved=False,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.post("/api/explain", response_model=ExplanationResponse)
async def explain_topic(request: ExplanationRequest):
    """
    Get educational explanation for a specific topic
    """
    try:
        logger.info(f"🎓 Explanation request from user: {request.user_id} for topic: {request.topic}")
        
        # Validate input
        if not request.topic or not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic is required and cannot be empty")
        
        if len(request.topic) > 1000:
            raise HTTPException(status_code=400, detail="Topic is too long (maximum 1000 characters)")
        
        # Check if explanation service is available
        if not explanation_agent or service_status["explanation"] != "healthy":
            raise HTTPException(status_code=503, detail="Explanation service is not available")
        
        # Generate explanation
        explanation_text = explanation_agent.get_explanation(request.topic, request.include_history)
        
        logger.info(f"✅ Explanation generated successfully for topic: {request.topic}")
        
        return ExplanationResponse(
            success=True,
            topic=request.topic,
            explanation=explanation_text,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Explanation endpoint error: {e}")
        return ExplanationResponse(
            success=False,
            topic=request.topic,
            explanation="",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/api/status")
async def status_check():
    """Detailed status check endpoint with cache statistics"""
    cache_stats = cache_instance.get_stats()
    return {
        "status": "operational",
        "services": service_status,
        "cache": cache_stats,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear the backend cache (admin endpoint)"""
    try:
        cache_instance.clear()
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/quiz/generate", response_model=QuizGenerationResponse)
async def generate_quiz(request: QuizGenerationRequest):
    """
    Generate a quiz on Google Forms based on topic and difficulty
    """
    try:
        logger.info(f"🎯 Quiz generation request from user: {request.user_id} for topic: '{request.topic}', difficulty: '{request.difficulty}'")
        
        # Validate input
        if not request.topic or not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic is required and cannot be empty")
        
        if not request.difficulty or request.difficulty.lower() not in ["easy", "medium", "hard"]:
            raise HTTPException(status_code=400, detail="Difficulty must be one of: easy, medium, hard")
        
        if len(request.topic) > 100:
            raise HTTPException(status_code=400, detail="Topic must be 100 characters or less")
        
        # Generate the quiz
        result = create_quiz(request.topic.strip(), request.difficulty.lower())
        
        if result["success"]:
            logger.info(f"✅ Quiz generated successfully: {result.get('quiz_info', {}).get('form_id', 'Unknown ID')}")
        else:
            logger.error(f"❌ Quiz generation failed: {result.get('error', 'Unknown error')}")
        
        return QuizGenerationResponse(
            success=result["success"],
            quiz_info=result.get("quiz_info"),
            message=result.get("message"),
            error=result.get("error"),
            details=result.get("details"),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Quiz generation endpoint error: {e}")
        return QuizGenerationResponse(
            success=False,
            error="Internal server error",
            details=[str(e)],
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/quiz/requirements")
async def get_quiz_requirements_endpoint():
    """
    Get the requirements and specifications for quiz generation
    """
    try:
        requirements = get_quiz_requirements()
        return {
            "success": True,
            "requirements": requirements,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Quiz requirements endpoint error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/debug/translate")
async def debug_translation(request: dict):
    """Debug endpoint for testing Arabic translation"""
    try:
        text = request.get("text", "")
        target_lang = request.get("target_language", "ar")
        
        logger.info(f"Debug translation request: '{text}' -> {target_lang}")
        
        # Test input translation
        input_result = process_with_moderation(text)
        
        # Test output translation if input was successful
        output_result = None
        if input_result.get("success") and input_result.get("original_language_code"):
            sample_response = "Hello! This is a test response from the AI system."
            output_result = translate_response_to_user_language(
                response_text=sample_response,
                target_language_code=input_result["original_language_code"]
            )
        
        return {
            "success": True,
            "input_processing": input_result,
            "output_translation": output_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug translation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("🌍🛡️🎓 EdRoom Language Bridge & Content Moderation API Server")
    print("=" * 60)
    print("Backend API Server - FastAPI")
    print()
    print("📋 API Endpoints:")
    print("  🏠 Root: http://localhost:8000/")
    print("  📚 Docs: http://localhost:8000/docs")
    print("  🏥 Health: http://localhost:8000/health")
    print("  🔧 Process: http://localhost:8000/api/process")
    print("  💬 Chat: http://localhost:8000/api/chat")
    print("  🎓 Explain: http://localhost:8000/api/explain")
    print("  🎯 Quiz Generate: http://localhost:8000/api/quiz/generate")
    print("  📋 Quiz Requirements: http://localhost:8000/api/quiz/requirements")
    print("  📈 Status: http://localhost:8000/api/status")
    print()
    print("🎨 Frontend (React):")
    print("  Run separately: cd ui && npm run dev")
    print("  Typical URL: http://localhost:5173")
    print()
    # Check environment variables
    missing_vars = []
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if missing_vars:
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("The API may not function properly without proper credentials.")
        print()
    
    print("🚀 Starting FastAPI server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
