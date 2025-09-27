"""
Quiz Generation Agent for EdRoom
Integrates with Google Forms API to create quizzes based on user input
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Add the quiz folder to the Python path
quiz_path = Path(__file__).parent / "quiz"
sys.path.insert(0, str(quiz_path))

try:
    from src.quiz_agent.generator import generate_mcqs, MCQ
    from src.quiz_agent.forms_api import create_quiz_form
    from src.quiz_agent.config import QUIZ_TITLE_PREFIX
except ImportError as e:
    logging.error(f"Failed to import quiz modules: {e}")
    raise

logger = logging.getLogger(__name__)

class QuizGenerationAgent:
    """Agent for generating quizzes on Google Forms"""
    
    def __init__(self):
        self.valid_difficulties = ["easy", "medium", "hard"]
    
    def validate_inputs(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Validate user inputs for quiz generation"""
        errors = []
        
        if not topic or not topic.strip():
            errors.append("Topic is required and cannot be empty")
        
        if not difficulty or difficulty.lower() not in self.valid_difficulties:
            errors.append(f"Difficulty must be one of: {', '.join(self.valid_difficulties)}")
        
        if len(topic.strip()) > 100:
            errors.append("Topic must be 100 characters or less")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def generate_quiz(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a quiz on Google Forms based on topic and difficulty
        
        Args:
            topic: The topic for the quiz
            difficulty: The difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary containing quiz information or error details
        """
        try:
            # Validate inputs
            validation = self.validate_inputs(topic, difficulty)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Invalid inputs",
                    "details": validation["errors"]
                }
            
            # Clean and prepare inputs
            topic = topic.strip()
            difficulty = difficulty.lower()
            
            logger.info(f"Generating quiz for topic: '{topic}', difficulty: '{difficulty}'")
            
            # Generate MCQs using the existing quiz agent
            mcqs = generate_mcqs(topic, difficulty)
            
            if not mcqs or len(mcqs) == 0:
                return {
                    "success": False,
                    "error": "Failed to generate quiz questions",
                    "details": ["No questions were generated. Please try again with a different topic."]
                }
            
            # Check if we have a reasonable number of questions
            if len(mcqs) < 10:
                logger.warning(f"Only generated {len(mcqs)} questions, which is less than ideal")
                # Still proceed but with a warning in the response
            
            # Create the quiz title and description
            title = f"{QUIZ_TITLE_PREFIX}: {topic.title()} ({difficulty.title()})"
            description = f"Auto-generated quiz on {topic} at {difficulty} difficulty level. This quiz contains {len(mcqs)} multiple-choice questions."
            
            # Create the Google Form
            form_info = create_quiz_form(
                title=title,
                description=description,
                mcqs=[mcq.model_dump() for mcq in mcqs]
            )
            
            logger.info(f"Successfully created quiz with form ID: {form_info['formId']}")
            
            # Create appropriate success message
            if len(mcqs) == 20:
                message = f"Quiz successfully created! {len(mcqs)} questions generated."
            elif len(mcqs) < 20:
                message = f"Quiz successfully created! {len(mcqs)} questions generated (filtered from AI output to ensure quality)."
            else:
                message = f"Quiz successfully created! {len(mcqs)} questions generated (filtered to best questions)."
            
            return {
                "success": True,
                "quiz_info": {
                    "form_id": form_info["formId"],
                    "responder_url": form_info["responderUri"],
                    "title": title,
                    "description": description,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_count": len(mcqs),
                    "created_at": form_info.get("created", {}).get("info", {}).get("title", "")
                },
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return {
                "success": False,
                "error": "Quiz generation failed",
                "details": [str(e)]
            }
    
    def get_quiz_requirements(self) -> Dict[str, Any]:
        """Get the requirements for quiz generation"""
        return {
            "required_fields": ["topic", "difficulty"],
            "topic_requirements": {
                "type": "string",
                "min_length": 1,
                "max_length": 100,
                "description": "The subject or topic for the quiz questions"
            },
            "difficulty_options": {
                "type": "enum",
                "values": self.valid_difficulties,
                "description": "The difficulty level for the quiz questions"
            },
            "output": {
                "question_count": 20,
                "question_type": "multiple_choice",
                "options_per_question": 4,
                "platform": "Google Forms"
            }
        }

# Create a global instance for easy import
quiz_agent = QuizGenerationAgent()

def create_quiz(topic: str, difficulty: str) -> Dict[str, Any]:
    """
    Convenience function to create a quiz
    
    Args:
        topic: The topic for the quiz
        difficulty: The difficulty level (easy, medium, hard)
        
    Returns:
        Dictionary containing quiz information or error details
    """
    return quiz_agent.generate_quiz(topic, difficulty)

def get_quiz_requirements() -> Dict[str, Any]:
    """Get the requirements for quiz generation"""
    return quiz_agent.get_quiz_requirements()
