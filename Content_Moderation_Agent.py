"""
Content Moderation Agent - Created by Claude
A LangGraph-based agent that moderates content for inappropriate material using ChatOpenAI
"""

import os
from typing import Dict, Any, TypedDict, Optional, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModerationState(TypedDict):
    """State schema for the Content Moderation Agent"""
    input_text: str
    moderation_result: Dict[str, Any]
    approved: bool
    confidence: float
    flagged_categories: List[str]
    explanation: str
    error: Optional[str]
    step: str
    metadata: Dict[str, Any]

class ContentModerationAgent:
    """
    Claude-powered LangGraph agent for content moderation using ChatOpenAI
    
    This agent uses a structured workflow to:
    1. Validate input text
    2. Analyze content for inappropriate material
    3. Classify content categories
    4. Provide detailed moderation results
    5. Return approval status with explanation
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize the Content Moderation Agent
        
        Args:
            model_name (str): OpenAI model to use (default: gpt-4o-mini)
            temperature (float): Temperature for the model (default: 0.1 for consistency)
        """
        logger.info(f"Initializing Content Moderation Agent with {model_name}...")
        
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        try:
            # Initialize ChatOpenAI
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=1000
            )
            logger.info(f"✅ ChatOpenAI initialized successfully with {model_name}!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChatOpenAI: {e}")
            raise
        
        # Build the workflow graph
        self.graph = self._build_workflow_graph()
        logger.info("Content Moderation Agent initialized successfully!")
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow with all processing nodes"""
        logger.info("Building Content Moderation workflow...")
        
        # Create the state graph
        workflow = StateGraph(ModerationState)
        
        # Add processing nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("analyze_content", self._analyze_content_node)
        workflow.add_node("classify_content", self._classify_content_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("finalize_result", self._finalize_result_node)
        
        # Set the entry point
        workflow.set_entry_point("validate_input")
        
        # Define the workflow edges
        workflow.add_edge("validate_input", "analyze_content")
        workflow.add_edge("analyze_content", "classify_content")
        workflow.add_edge("classify_content", "make_decision")
        workflow.add_edge("make_decision", "finalize_result")
        workflow.add_edge("finalize_result", END)
        
        compiled_graph = workflow.compile()
        logger.info("Content Moderation workflow built successfully!")
        return compiled_graph
    
    def _validate_input_node(self, state: ModerationState) -> ModerationState:
        """Node 1: Validate the input text"""
        logger.info("🔍 Step 1: Validating input text...")
        
        input_text = state.get("input_text", "").strip()
        
        if not input_text:
            logger.warning("Input validation failed: Empty or whitespace-only text")
            state.update({
                "error": "Input text is empty or contains only whitespace",
                "step": "validation_failed",
                "approved": False,
                "metadata": {"validation_error": "empty_input"}
            })
            return state
        
        if len(input_text) > 10000:  # Reasonable limit for moderation
            logger.warning("Input validation failed: Text too long")
            state.update({
                "error": "Input text is too long (maximum 10,000 characters)",
                "step": "validation_failed",
                "approved": False,
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
    
    def _analyze_content_node(self, state: ModerationState) -> ModerationState:
        """Node 2: Analyze content for inappropriate material"""
        logger.info("🔍 Step 2: Analyzing content for inappropriate material...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        try:
            # Create system message for content moderation
            system_message = SystemMessage(content="""
You are a professional content moderation AI. Your job is to analyze text content and identify any inappropriate material.

Analyze the provided text for the following categories of inappropriate content:
1. VULGAR: Profanity, crude language, offensive words
2. SEXUAL: Sexual content, adult themes, inappropriate sexual references
3. HATEFUL: Hate speech, discrimination, harassment based on race, gender, religion, etc.
4. VIOLENT: Graphic violence, threats, harmful content
5. HARASSMENT: Bullying, personal attacks, intimidation
6. ILLEGAL: Content promoting illegal activities
7. SPAM: Repetitive, promotional, or spam-like content
8. MISINFORMATION: False or misleading information that could cause harm

Respond with a JSON object containing:
{
    "analysis": "Detailed analysis of the content",
    "inappropriate_categories": ["list", "of", "flagged", "categories"],
    "severity_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "explanation": "Clear explanation of why content was flagged or approved"
}

Be thorough but fair. Consider context and intent. Minor profanity in casual conversation may be acceptable, but hate speech or explicit sexual content should be flagged.
""")
            
            human_message = HumanMessage(content=f"Please analyze this text for inappropriate content:\n\n{state['input_text']}")
            
            # Get response from ChatOpenAI
            response = self.llm.invoke([system_message, human_message])
            
            # Parse the JSON response
            try:
                moderation_result = json.loads(response.content)
                logger.info("✅ Content analysis completed successfully")
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON response, using fallback analysis")
                moderation_result = {
                    "analysis": response.content,
                    "inappropriate_categories": [],
                    "severity_score": 0.0,
                    "confidence": 0.5,
                    "explanation": "Analysis completed but response format was unexpected"
                }
            
            state.update({
                "moderation_result": moderation_result,
                "step": "content_analyzed",
                "metadata": {
                    **state.get("metadata", {}),
                    "analysis_method": "chatopenai",
                    "model_response": response.content[:500]  # Store first 500 chars
                }
            })
            
        except Exception as e:
            error_msg = f"Content analysis failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "step": "analysis_failed",
                "approved": False,
                "metadata": {
                    **state.get("metadata", {}),
                    "analysis_error": str(e)
                }
            })
        
        return state
    
    def _classify_content_node(self, state: ModerationState) -> ModerationState:
        """Node 3: Classify content and extract categories"""
        logger.info("📋 Step 3: Classifying content categories...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        try:
            moderation_result = state.get("moderation_result", {})
            
            # Extract flagged categories
            flagged_categories = moderation_result.get("inappropriate_categories", [])
            severity_score = moderation_result.get("severity_score", 0.0)
            confidence = moderation_result.get("confidence", 0.0)
            explanation = moderation_result.get("explanation", "No explanation provided")
            
            logger.info(f"✅ Content classified - Categories: {flagged_categories}, Severity: {severity_score:.2f}")
            
            state.update({
                "flagged_categories": flagged_categories,
                "confidence": confidence,
                "explanation": explanation,
                "step": "content_classified",
                "metadata": {
                    **state.get("metadata", {}),
                    "severity_score": severity_score,
                    "num_flagged_categories": len(flagged_categories)
                }
            })
            
        except Exception as e:
            error_msg = f"Content classification failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "step": "classification_failed",
                "approved": False,
                "metadata": {
                    **state.get("metadata", {}),
                    "classification_error": str(e)
                }
            })
        
        return state
    
    def _make_decision_node(self, state: ModerationState) -> ModerationState:
        """Node 4: Make final approval decision"""
        logger.info("⚖️ Step 4: Making moderation decision...")
        
        # Skip if there's already an error
        if state.get("error"):
            return state
        
        try:
            flagged_categories = state.get("flagged_categories", [])
            severity_score = state.get("metadata", {}).get("severity_score", 0.0)
            confidence = state.get("confidence", 0.0)
            
            # Decision logic: approve if no flagged categories and low severity
            approved = len(flagged_categories) == 0 and severity_score < 0.3
            
            # Log decision
            if approved:
                logger.info("✅ Content APPROVED - No inappropriate material detected")
            else:
                logger.info(f"❌ Content REJECTED - Flagged categories: {flagged_categories}")
            
            state.update({
                "approved": approved,
                "step": "decision_made",
                "metadata": {
                    **state.get("metadata", {}),
                    "decision_logic": "no_flags_and_low_severity",
                    "decision_threshold": 0.3
                }
            })
            
        except Exception as e:
            error_msg = f"Decision making failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "step": "decision_failed",
                "approved": False,
                "metadata": {
                    **state.get("metadata", {}),
                    "decision_error": str(e)
                }
            })
        
        return state
    
    def _finalize_result_node(self, state: ModerationState) -> ModerationState:
        """Node 5: Finalize the moderation result"""
        logger.info("📋 Step 5: Finalizing moderation result...")
        
        state.update({
            "step": "moderation_complete",
            "metadata": {
                **state.get("metadata", {}),
                "processing_completed": True,
                "final_step": "finalize_result"
            }
        })
        
        if state.get("error"):
            logger.error("❌ Moderation completed with errors")
        else:
            logger.info("✅ Moderation completed successfully!")
        
        return state
    
    def moderate_content(self, input_text: str) -> Dict[str, Any]:
        """
        Main method to moderate content through the Content Moderation Agent
        
        Args:
            input_text (str): The text to moderate
            
        Returns:
            Dict[str, Any]: Comprehensive moderation result
        """
        logger.info("🚀 Starting Content Moderation Agent processing...")
        
        # Initialize the agent state
        initial_state = ModerationState(
            input_text=input_text,
            moderation_result={},
            approved=False,
            confidence=0.0,
            flagged_categories=[],
            explanation="",
            error=None,
            step="initialized",
            metadata={"agent_version": "claude_v1_openai", "start_time": "processing"}
        )
        
        try:
            # Execute the workflow graph
            final_state = self.graph.invoke(initial_state)
            
            # Prepare the response
            success = not bool(final_state.get("error"))
            
            result = {
                "success": success,
                "input_text": final_state["input_text"],
                "approved": final_state.get("approved", False),
                "confidence": final_state.get("confidence", 0.0),
                "flagged_categories": final_state.get("flagged_categories", []),
                "explanation": final_state.get("explanation", ""),
                "moderation_result": final_state.get("moderation_result", {}),
                "error": final_state.get("error"),
                "processing_step": final_state.get("step", "unknown"),
                "metadata": final_state.get("metadata", {})
            }
            
            if success:
                status = "APPROVED" if result["approved"] else "REJECTED"
                logger.info(f"🎉 Content Moderation completed successfully! Status: {status}")
            else:
                logger.error(f"💥 Moderation failed at step '{result['processing_step']}': {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(f"💥 {error_msg}")
            
            return {
                "success": False,
                "input_text": input_text,
                "approved": False,
                "confidence": 0.0,
                "flagged_categories": [],
                "explanation": "Moderation workflow failed",
                "moderation_result": {},
                "error": error_msg,
                "processing_step": "workflow_execution_failed",
                "metadata": {"execution_error": str(e)}
            }

def create_content_moderation_agent(model_name: str = "gpt-4o-mini", temperature: float = 0.1) -> ContentModerationAgent:
    """
    Factory function to create a new Content Moderation Agent instance
    
    Args:
        model_name (str): OpenAI model to use
        temperature (float): Temperature for the model
    
    Returns:
        ContentModerationAgent: A new agent instance ready for processing
    """
    return ContentModerationAgent(model_name=model_name, temperature=temperature)

# Demonstration and testing
if __name__ == "__main__":
    print("🛡️ Content Moderation Agent - Claude Edition with ChatOpenAI")
    print("=" * 80)
    print("Demonstrating content moderation capabilities\n")
    
    try:
        # Create the agent
        agent = create_content_moderation_agent()
        
        # Test cases covering various content types
        test_cases = [
            ("Hello, how are you today?", "Clean, friendly text"),
            ("This is a great product! I highly recommend it.", "Positive review"),
            ("Fuck this stupid shit!", "Mild profanity/negative sentiment"),
            ("You're an idiot and should go kill yourself", "Harassment/threats"),
            ("Check out this adult content at this porn website", "Sexual/adult content"),
            ("All people of [group] are terrible", "Hate speech"),
            ("Buy now! Limited time offer! Click here!", "Spam/promotional"),
            ("", "Empty input (should fail)"),
            ("The weather is nice today.", "Neutral, safe content"),
            ("I disagree with your opinion, but respect your right to have it.", "Respectful disagreement"),
        ]
        
        print(f"Running {len(test_cases)} test cases...\n")
        
        for i, (text, description) in enumerate(test_cases, 1):
            print(f"Test {i}: {description}")
            print(f"Input: '{text}'")
            
            result = agent.moderate_content(text)
            
            if result["success"]:
                status = "✅ APPROVED" if result["approved"] else "❌ REJECTED"
                print(f"{status}")
                print(f"📊 Confidence: {result['confidence']:.1%}")
                if result['flagged_categories']:
                    print(f"🚩 Flagged Categories: {', '.join(result['flagged_categories'])}")
                print(f"💬 Explanation: {result['explanation']}")
            else:
                print(f"❌ Error: {result['error']}")
            
            print("-" * 80)
        
        print("\n🎯 Demo completed! The Content Moderation Agent is ready for use.")
        print("💡 Use create_content_moderation_agent() to create your own instance.")
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("\n🔧 Setup Instructions:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Install required dependencies: pip install -r requirements.txt")
        print("3. Ensure you have OpenAI API credits available")
        print("\n📚 Documentation: https://platform.openai.com/docs")
