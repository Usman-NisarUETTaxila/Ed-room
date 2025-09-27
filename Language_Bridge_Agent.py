"""
Language Bridge Agent - Created by Claude
A LangGraph-based agent that detects language and translates text to English using Google Cloud Translation API
"""

import os
from typing import Dict, Any, TypedDict, Optional
from google.cloud import translate_v2 as translate
from langgraph.graph import StateGraph, END
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State schema for the Language Bridge Agent"""
    input_text: str
    detected_language: str
    detected_language_code: str
    confidence: float
    translated_text: str
    is_english: bool
    error: Optional[str]
    step: str
    metadata: Dict[str, Any]

class LanguageBridgeAgent:
    """
    Claude-powered LangGraph agent for language detection and translation using Google Cloud Translation API
    
    This agent uses a structured workflow to:
    1. Validate input text
    2. Detect the source language
    3. Check if translation is needed
    4. Translate to English if necessary
    5. Return comprehensive results
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the agent with Google Cloud Translation API
        
        Args:
            credentials_path (Optional[str]): Path to Google Cloud service account JSON file.
                                            If None, will use GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        logger.info("Initializing Language Bridge Agent with Google Cloud Translation API...")
        
        # Set up Google Cloud credentials if provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            # Initialize Google Cloud Translation client
            self.translate_client = translate.Client()
            logger.info("✅ Google Cloud Translation client initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud Translation client: {e}")
            logger.info("💡 Make sure to set GOOGLE_APPLICATION_CREDENTIALS or provide credentials_path")
            raise
        
        # Build the workflow graph
        self.graph = self._build_workflow_graph()
        logger.info("Language Bridge Agent initialized successfully!")
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow with all processing nodes"""
        logger.info("Building LangGraph workflow...")
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add processing nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("detect_language", self._detect_language_node)
        workflow.add_node("check_english", self._check_english_node)
        workflow.add_node("translate_text", self._translate_text_node)
        workflow.add_node("finalize_output", self._finalize_output_node)
        
        # Set the entry point
        workflow.set_entry_point("validate_input")
        
        # Define the workflow edges
        workflow.add_edge("validate_input", "detect_language")
        workflow.add_edge("detect_language", "check_english")
        
        # Conditional routing based on language detection
        workflow.add_conditional_edges(
            "check_english",
            self._routing_decision,
            {
                "needs_translation": "translate_text",
                "already_english": "finalize_output",
                "error": "finalize_output"
            }
        )
        
        workflow.add_edge("translate_text", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        compiled_graph = workflow.compile()
        logger.info("LangGraph workflow built successfully!")
        return compiled_graph
    
    def _validate_input_node(self, state: AgentState) -> AgentState:
        """Node 1: Validate the input text"""
        logger.info("🔍 Step 1: Validating input text...")
        
        input_text = state.get("input_text", "").strip()
        
        if not input_text:
            logger.warning("Input validation failed: Empty or whitespace-only text")
            state.update({
                "error": "Input text is empty or contains only whitespace",
                "step": "validation_failed",
                "metadata": {"validation_error": "empty_input"}
            })
            return state
        
        if len(input_text) > 30000:  # Google Cloud Translation API limit
            logger.warning("Input validation failed: Text too long")
            state.update({
                "error": "Input text is too long (maximum 30,000 characters for Google Cloud Translation)",
                "step": "validation_failed",
                "metadata": {"validation_error": "text_too_long", "length": len(input_text)}
            })
            return state
        
        logger.info(f"✅ Input validated successfully: '{input_text[:50]}{'...' if len(input_text) > 50 else ''}'")
        state.update({
            "step": "input_validated",
            "error": None,
            "metadata": {"input_length": len(input_text), "input_preview": input_text[:100]}
        })
        
        return state
    
    def _detect_language_node(self, state: AgentState) -> AgentState:
        """Node 2: Detect the language of the input text"""
        logger.info("🌐 Step 2: Detecting language...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        try:
            # Perform language detection using Google Cloud Translation API
            detection_result = self.translate_client.detect_language(state["input_text"])
            
            detected_code = detection_result['language']
            confidence = detection_result['confidence']
            
            # Get language name from Google Cloud Translation API
            languages = self.translate_client.get_languages(target_language='en')
            language_name = next(
                (lang['name'] for lang in languages if lang['language'] == detected_code),
                f"Language ({detected_code})"
            )
            
            logger.info(f"✅ Language detected: {language_name} ({detected_code}) with {confidence:.2%} confidence")
            
            state.update({
                "detected_language_code": detected_code,
                "detected_language": language_name,
                "confidence": confidence,
                "step": "language_detected",
                "metadata": {
                    **state.get("metadata", {}),
                    "detection_confidence": confidence,
                    "detection_method": "google_cloud_translate",
                    "detection_result": detection_result
                }
            })
            
        except Exception as e:
            error_msg = f"Language detection failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "step": "detection_failed",
                "metadata": {
                    **state.get("metadata", {}),
                    "detection_error": str(e)
                }
            })
        
        return state
    
    def _check_english_node(self, state: AgentState) -> AgentState:
        """Node 3: Check if the detected language is English"""
        logger.info("🔤 Step 3: Checking if text is in English...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        detected_code = state.get("detected_language_code", "")
        is_english = detected_code.lower() == "en"
        
        state.update({
            "is_english": is_english,
            "step": "english_check_complete"
        })
        
        if is_english:
            logger.info("✅ Text is already in English - no translation needed")
            state["translated_text"] = state["input_text"]
        else:
            logger.info(f"🔄 Text is in {state.get('detected_language', 'unknown language')} - translation required")
        
        return state
    
    def _routing_decision(self, state: AgentState) -> str:
        """Determine the next step based on current state"""
        if state.get("error"):
            return "error"
        elif state.get("is_english", False):
            return "already_english"
        else:
            return "needs_translation"
    
    def _translate_text_node(self, state: AgentState) -> AgentState:
        """Node 4: Translate the text to English"""
        logger.info("🔄 Step 4: Translating text to English...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        try:
            # Perform translation using Google Cloud Translation API
            translation_result = self.translate_client.translate(
                state["input_text"],
                source_language=state["detected_language_code"],
                target_language="en"
            )
            
            translated_text = translation_result['translatedText']
            
            logger.info(f"✅ Translation completed: '{translated_text[:50]}{'...' if len(translated_text) > 50 else ''}'")
            
            state.update({
                "translated_text": translated_text,
                "step": "translation_complete",
                "metadata": {
                    **state.get("metadata", {}),
                    "translation_service": "google_cloud_translate",
                    "source_language": state["detected_language_code"],
                    "target_language": "en",
                    "translation_result": translation_result
                }
            })
            
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "step": "translation_failed",
                "metadata": {
                    **state.get("metadata", {}),
                    "translation_error": str(e)
                }
            })
        
        return state
    
    def _finalize_output_node(self, state: AgentState) -> AgentState:
        """Node 5: Finalize the output and prepare results"""
        logger.info("📋 Step 5: Finalizing output...")
        
        state.update({
            "step": "processing_complete",
            "metadata": {
                **state.get("metadata", {}),
                "processing_completed": True,
                "final_step": "finalize_output"
            }
        })
        
        if state.get("error"):
            logger.error("❌ Processing completed with errors")
        else:
            logger.info("✅ Processing completed successfully!")
        
        return state
    
    def process_text(self, input_text: str) -> Dict[str, Any]:
        """
        Main method to process text through the Language Bridge Agent
        
        Args:
            input_text (str): The text to detect language and translate
            
        Returns:
            Dict[str, Any]: Comprehensive result with detection, translation, and metadata
        """
        logger.info("🚀 Starting Language Bridge Agent processing...")
        
        # Initialize the agent state
        initial_state = AgentState(
            input_text=input_text,
            detected_language="",
            detected_language_code="",
            confidence=0.0,
            translated_text="",
            is_english=False,
            error=None,
            step="initialized",
            metadata={"agent_version": "claude_v2_google_cloud", "start_time": "processing"}
        )
        
        try:
            # Execute the workflow graph
            final_state = self.graph.invoke(initial_state)
            
            # Prepare the response
            success = not bool(final_state.get("error"))
            
            result = {
                "success": success,
                "input_text": final_state["input_text"],
                "detected_language": final_state.get("detected_language", ""),
                "detected_language_code": final_state.get("detected_language_code", ""),
                "confidence": final_state.get("confidence", 0.0),
                "translated_text": final_state.get("translated_text", ""),
                "is_english": final_state.get("is_english", False),
                "error": final_state.get("error"),
                "processing_step": final_state.get("step", "unknown"),
                "metadata": final_state.get("metadata", {})
            }
            
            if success:
                logger.info("🎉 Language Bridge Agent processing completed successfully!")
            else:
                logger.error(f"💥 Processing failed at step '{result['processing_step']}': {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(f"💥 {error_msg}")
            
            return {
                "success": False,
                "input_text": input_text,
                "detected_language": "",
                "detected_language_code": "",
                "confidence": 0.0,
                "translated_text": "",
                "is_english": False,
                "error": error_msg,
                "processing_step": "workflow_execution_failed",
                "metadata": {"execution_error": str(e)}
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages from Google Cloud Translation API
        
        Returns:
            Dict[str, str]: Dictionary mapping language codes to language names
        """
        try:
            languages = self.translate_client.get_languages(target_language='en')
            # Handle both possible response formats
            if languages and len(languages) > 0:
                first_lang = languages[0]
                if 'language' in first_lang:  # Format: {'language': 'ar', 'name': 'Arabic'}
                    return {lang['language']: lang['name'] for lang in languages}
                elif 'languageCode' in first_lang:  # Format: {'languageCode': 'ar', 'name': 'Arabic'}
                    return {lang['languageCode']: lang['name'] for lang in languages}
            return {}
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {}
    
    def translate_to_language(self, text: str, target_language_code: str, source_language_code: str = 'en') -> Dict[str, Any]:
        """
        Translate text from one language to another using Google Cloud Translation API
        
        Args:
            text (str): The text to translate
            target_language_code (str): Target language code (e.g., 'es', 'fr', 'de', 'ar')
            source_language_code (str): Source language code (default: 'en')
            
        Returns:
            Dict[str, Any]: Translation result with success status and translated text
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for translation")
                return {
                    "success": False,
                    "error": "Empty text provided",
                    "translated_text": ""
                }
            
            # Skip translation if source and target are the same
            if source_language_code.lower() == target_language_code.lower():
                logger.info(f"Skipping translation - same language: {source_language_code}")
                return {
                    "success": True,
                    "translated_text": text,
                    "source_language": source_language_code,
                    "target_language": target_language_code,
                    "skipped": True
                }
            
            logger.info(f"Translating from {source_language_code} to {target_language_code}")
            logger.info(f"Text to translate: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            # Perform translation using Google Cloud Translation API
            translation_result = self.translate_client.translate(
                text,
                source_language=source_language_code,
                target_language=target_language_code
            )
            
            translated_text = translation_result['translatedText']
            
            logger.info(f"✅ Translation completed successfully")
            logger.info(f"Original: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            logger.info(f"Translated: '{translated_text[:50]}{'...' if len(translated_text) > 50 else ''}'")
            
            return {
                "success": True,
                "translated_text": translated_text,
                "source_language": source_language_code,
                "target_language": target_language_code,
                "original_text": text,
                "translation_result": translation_result
            }
            
        except Exception as e:
            error_msg = f"Translation failed from {source_language_code} to {target_language_code}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Failed text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            return {
                "success": False,
                "error": error_msg,
                "translated_text": text  # Return original text as fallback
            }

def create_language_bridge_agent(credentials_path: Optional[str] = None) -> LanguageBridgeAgent:
    """
    Factory function to create a new Language Bridge Agent instance
    
{{ ... }}
    Args:
        credentials_path (Optional[str]): Path to Google Cloud service account JSON file
    
    Returns:
        LanguageBridgeAgent: A new agent instance ready for processing
    """
    return LanguageBridgeAgent(credentials_path=credentials_path)

# Integrated Translation and Moderation Function
def clean_formatting_for_translation(text: str) -> str:
    """
    Remove formatting elements that don't translate well to other languages
    
    Args:
        text (str): Text with English formatting
        
    Returns:
        str: Clean text suitable for translation
    """
    import re
    
    # Remove markdown bold formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove emojis and special characters that don't translate well
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove specific formatting symbols that are English-centric
    text = re.sub(r'[✅❌⚠️🎯🎓📝📄🏆🏅💬🔍🌐🛡️📚📊🎨🚀]', '', text)
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Keep paragraph breaks but clean up
    text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
    text = text.strip()
    
    return text

def translate_response_to_user_language(response_text: str, target_language_code: str, credentials_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Translate AI response back to user's original language with clean formatting
    
    Args:
        response_text (str): The AI response text in English
        target_language_code (str): User's original language code (e.g., 'ar', 'es', 'fr')
        credentials_path (Optional[str]): Path to Google Cloud credentials
        
    Returns:
        Dict[str, Any]: Translation result
    """
    try:
        logger.info(f"Starting translation to user language: {target_language_code}")
        logger.info(f"Response text length: {len(response_text)} characters")
        
        # Initialize the Language Bridge Agent
        agent = LanguageBridgeAgent(credentials_path)
        
        # Skip translation and cleaning if target is English - preserve original formatting
        if target_language_code.lower() in ['en', 'english']:
            logger.info("Skipping translation - target is English, preserving original formatting")
            return {
                "success": True,
                "translated_text": response_text,  # Keep original formatting for English
                "skipped": True,
                "target_language": target_language_code
            }
        
        # Validate target language code
        if not target_language_code or len(target_language_code.strip()) == 0:
            logger.error("Invalid target language code provided")
            return {
                "success": False,
                "error": "Invalid target language code",
                "translated_text": response_text
            }
        
        logger.info(f"Proceeding with translation to non-English language: {target_language_code}")
        
        # ONLY clean formatting for non-English languages (not English)
        # This preserves rich formatting for English users
        clean_text = clean_formatting_for_translation(response_text)
        logger.info(f"Original text length: {len(response_text)}")
        logger.info(f"Cleaned text length: {len(clean_text)}")
        logger.info(f"Original text preview: '{response_text[:100]}{'...' if len(response_text) > 100 else ''}'")
        logger.info(f"Cleaned text preview: '{clean_text[:100]}{'...' if len(clean_text) > 100 else ''}'")
        
        # If cleaning removed too much content, use original text
        if len(clean_text.strip()) < 10:  # If cleaned text is too short
            logger.warning("Cleaned text too short, using original text for translation")
            text_to_translate = response_text
        else:
            text_to_translate = clean_text
        
        # Translate the response to user's language
        translation_result = agent.translate_to_language(
            text=text_to_translate,
            target_language_code=target_language_code,
            source_language_code='en'
        )
        
        logger.info(f"Translation completed with result: {translation_result.get('success', False)}")
        
        return translation_result
        
    except Exception as e:
        logger.error(f"Failed to translate response to user language {target_language_code}: {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "translated_text": response_text  # Return original as fallback
        }

def process_with_moderation(input_text: str, credentials_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Process text through translation and content moderation pipeline
    
    Args:
        input_text (str): The text to translate and moderate
        credentials_path (Optional[str]): Path to Google Cloud credentials
        
    Returns:
        Dict[str, Any]: Comprehensive result with translation and moderation
    """
    try:
        # Import content moderation agent
        from Content_Moderation_Agent import create_content_moderation_agent
        
        # Initialize both agents
        translation_agent = create_language_bridge_agent(credentials_path)
        moderation_agent = create_content_moderation_agent()
        
        logger.info("🚀 Starting integrated translation and moderation process...")
        
        # Step 1: Translate the text
        logger.info("🌐 Step 1: Processing translation...")
        translation_result = translation_agent.process_text(input_text)
        
        if not translation_result["success"]:
            return {
                "success": False,
                "input_text": input_text,
                "translation_result": translation_result,
                "moderation_result": {},
                "final_approved": False,
                "error": f"Translation failed: {translation_result['error']}",
                "step": "translation_failed"
            }
        
        # Step 2: Moderate the translated content
        logger.info("🛡️ Step 2: Processing content moderation...")
        translated_text = translation_result["translated_text"]
        moderation_result = moderation_agent.moderate_content(translated_text)
        
        if not moderation_result["success"]:
            return {
                "success": False,
                "input_text": input_text,
                "translation_result": translation_result,
                "moderation_result": moderation_result,
                "final_approved": False,
                "error": f"Moderation failed: {moderation_result['error']}",
                "step": "moderation_failed"
            }
        
        # Step 3: Make final decision
        final_approved = moderation_result["approved"]
        
        # Prepare comprehensive response
        result = {
            "success": True,
            "input_text": input_text,
            "original_language": translation_result["detected_language"],
            "original_language_code": translation_result["detected_language_code"],
            "translation_confidence": translation_result["confidence"],
            "translated_text": translation_result["translated_text"],
            "is_english": translation_result["is_english"],
            "moderation_approved": moderation_result["approved"],
            "moderation_confidence": moderation_result["confidence"],
            "flagged_categories": moderation_result["flagged_categories"],
            "moderation_explanation": moderation_result["explanation"],
            "final_approved": final_approved,
            "translation_result": translation_result,
            "moderation_result": moderation_result,
            "error": None,
            "step": "completed"
        }
        
        status = "APPROVED" if final_approved else "REJECTED"
        logger.info(f"✅ Integrated processing completed! Final Status: {status}")
        
        return result
        
    except Exception as e:
        error_msg = f"Integrated processing failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        return {
            "success": False,
            "input_text": input_text,
            "translation_result": {},
            "moderation_result": {},
            "final_approved": False,
            "error": error_msg,
            "step": "integration_failed"
        }

# Interactive main function
def interactive_translation_moderation():
    """Interactive function for translation and moderation"""
    print("🌍🛡️ Language Bridge Agent with Content Moderation")
    print("=" * 70)
    print("This system translates text to English and checks for inappropriate content")
    print("Type 'quit', 'exit', or 'q' to stop")
    print("Type 'help' for available commands\n")
    
    while True:
        try:
            # Get user input
            user_input = input("Enter text to translate and moderate: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("\n📋 Available Commands:")
                print("  - Enter any text to translate and moderate")
                print("  - 'quit' or 'exit' - Exit the program")
                print("  - 'help' - Show this help message\n")
                continue
            elif not user_input:
                print("⚠️  Please enter some text to process.\n")
                continue
            
            print(f"\n🔄 Processing: '{user_input}'")
            print("=" * 50)
            
            # Process the text through translation and moderation
            result = process_with_moderation(user_input)
            
            if result["success"]:
                # Show translation results
                print(f"🌐 Original Language: {result['original_language']} ({result['original_language_code']})")
                print(f"🔄 Translation Confidence: {result['translation_confidence']:.1%}")
                print(f"📝 Translated Text: '{result['translated_text']}'")
                
                if result['is_english']:
                    print("ℹ️  Text was already in English")
                
                print()  # Empty line for separation
                
                # Show moderation results
                moderation_status = "✅ APPROVED" if result["moderation_approved"] else "❌ REJECTED"
                print(f"🛡️ Content Moderation: {moderation_status}")
                print(f"📊 Moderation Confidence: {result['moderation_confidence']:.1%}")
                
                if result['flagged_categories']:
                    print(f"🚩 Flagged Categories: {', '.join(result['flagged_categories'])}")
                
                print(f"💬 Explanation: {result['moderation_explanation']}")
                
                print()  # Empty line for separation
                
                # Show final decision
                if result['final_approved']:
                    print("🎉 FINAL RESULT: ✅ APPROVED")
                    print("✅ Content has been translated and is appropriate for use.")
                else:
                    print("🚫 FINAL RESULT: ❌ REJECTED")
                    print("❌ Content contains inappropriate material and should not be used.")
                
            else:
                print(f"❌ Processing Error: {result['error']}")
                print(f"Failed at step: {result['step']}")
            
            print("\n" + "=" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}\n")

# Demonstration and testing
if __name__ == "__main__":
    print("🌍🛡️ Language Bridge Agent with Integrated Content Moderation")
    print("=" * 80)
    print("Claude Edition - Translation + Content Safety")
    print()
    
    # Check for required environment variables
    missing_vars = []
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n🔧 Setup Instructions:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS for translation")
        print("2. Set OPENAI_API_KEY for content moderation")
        print("3. Both are required for the integrated system")
        print("\nExiting...")
        exit(1)
    
    try:
        print("🔧 Initializing integrated system...")
        
        # Test the system first
        test_result = process_with_moderation("Hello, how are you?")
        if test_result["success"]:
            print("✅ System initialized successfully!\n")
            
            # Run interactive mode
            interactive_translation_moderation()
        else:
            print(f"❌ System initialization failed: {test_result['error']}")
            
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify Google Cloud credentials are valid")
        print("2. Verify OpenAI API key is valid")
        print("3. Check internet connection")
        print("4. Ensure all dependencies are installed")