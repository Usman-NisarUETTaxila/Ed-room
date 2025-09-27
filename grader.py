import os
import io
import base64
from langchain_openai import ChatOpenAI
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'  # manual path of tesseract if needed
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
import re
from typing import Dict, Any, Union, BinaryIO

load_dotenv()


class GradingResult(BaseModel):
    marks_obtained: int = Field(description="Numeric score obtained by the student")
    feedback: str = Field(description="Constructive feedback for the student")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file using pdfplumber with OCR fallback for scanned documents
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            # If scanned by camscanner detected (some cases)
            if not page_text or page_text.strip().lower() in ["camscanner", "scanned by camscanner"]:
                # Run OCR fallback
                img = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text.strip():
                    text += ocr_text + "\n"
            else:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_pdf_blob(pdf_blob: Union[bytes, BinaryIO, str]) -> str:
    """
    Extract text from PDF BLOB/bytes data using pdfplumber with OCR fallback for scanned documents
    
    Args:
        pdf_blob: PDF data as bytes, BinaryIO object, or base64 encoded string
        
    Returns:
        str: Extracted text from the PDF
    """
    text = ""
    
    try:
        # Handle different input types
        if isinstance(pdf_blob, str):
            # Assume it's base64 encoded
            try:
                pdf_bytes = base64.b64decode(pdf_blob)
            except Exception:
                raise ValueError("Invalid base64 encoded PDF data")
        elif isinstance(pdf_blob, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_blob)
        elif hasattr(pdf_blob, 'read'):
            # It's a file-like object
            pdf_bytes = pdf_blob.read()
            if hasattr(pdf_blob, 'seek'):
                pdf_blob.seek(0)  # Reset position for potential reuse
        else:
            raise ValueError("Unsupported PDF blob type. Expected bytes, BinaryIO, or base64 string")
        
        # Create BytesIO object from PDF bytes
        pdf_stream = io.BytesIO(pdf_bytes)
        
        # Extract text using pdfplumber
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                # If scanned by camscanner detected (some cases) or no text found
                if not page_text or page_text.strip().lower() in ["camscanner", "scanned by camscanner"]:
                    try:
                        # Run OCR fallback
                        img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip():
                            text += ocr_text + "\n"
                    except Exception as ocr_error:
                        print(f"OCR failed for page: {ocr_error}")
                        # Continue without OCR text
                        continue
                else:
                    text += page_text + "\n"
                    
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF blob: {str(e)}")
    
    return text.strip()


def clean_json(text: str) -> str:
    """
    Extract JSON from text that might be wrapped in markdown code blocks
    """
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)  # JSON inside fences
    return text


def grade_assignment(pdf_path: str, rubric: str, total_marks: int = 100) -> Dict[str, Any]:
    """
    Grade assignment from PDF file using LangChain with OpenAI
    
    Args:
        pdf_path: Path to the PDF file
        rubric: Grading rubric and criteria
        total_marks: Maximum marks possible
        
    Returns:
        Dict containing marks_obtained, total_marks, and ai_feedback
    """

    # Initialize LangChain LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Fixed model name
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2  # Lower temperature for more consistent grading
    )

    # Extract text from PDF
    assignment_text = extract_text_from_pdf(pdf_path)

    if not assignment_text:
        return {
            "marks_obtained": 0,
            "total_marks": total_marks,
            "ai_feedback": "No readable text found in the PDF (even with OCR). Please check the file."
        }

    return _grade_assignment_text(assignment_text, rubric, total_marks, llm)


def grade_assignment_from_blob(pdf_blob: Union[bytes, BinaryIO, str], rubric: str, total_marks: int = 100) -> Dict[str, Any]:
    """
    Grade assignment from PDF BLOB/bytes data using LangChain with OpenAI
    
    Args:
        pdf_blob: PDF data as bytes, BinaryIO object, or base64 encoded string
        rubric: Grading rubric and criteria
        total_marks: Maximum marks possible
        
    Returns:
        Dict containing marks_obtained, total_marks, and ai_feedback
    """

    # Initialize LangChain LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Fixed model name
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2  # Lower temperature for more consistent grading
    )

    try:
        # Extract text from PDF blob
        assignment_text = extract_text_from_pdf_blob(pdf_blob)

        if not assignment_text:
            return {
                "marks_obtained": 0,
                "total_marks": total_marks,
                "ai_feedback": "No readable text found in the PDF BLOB (even with OCR). Please check the file data."
            }

        return _grade_assignment_text(assignment_text, rubric, total_marks, llm)
        
    except Exception as e:
        return {
            "marks_obtained": 0,
            "total_marks": total_marks,
            "ai_feedback": f"Error processing PDF BLOB: {str(e)}"
        }


def _grade_assignment_text(assignment_text: str, rubric: str, total_marks: int, llm) -> Dict[str, Any]:
    """
    Internal function to grade assignment text using the provided LLM
    
    Args:
        assignment_text: Extracted text from the assignment
        rubric: Grading rubric and criteria
        total_marks: Maximum marks possible
        llm: LangChain LLM instance
        
    Returns:
        Dict containing marks_obtained, total_marks, and ai_feedback
    """
    
    # Set up structured output parser
    parser = PydanticOutputParser(pydantic_object=GradingResult)

    # Create prompt template using LangChain
    prompt_template = PromptTemplate(
        template="""
Here is the grading rubric and questions:
{rubric}

Assignment Text:
{assignment_text}

Please provide:
1. A numeric score out of {total_marks}
2. Short constructive feedback (3-4 sentences)

{format_instructions}
""",
        input_variables=["rubric", "assignment_text", "total_marks"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    # Format the prompt
    formatted_prompt = prompt_template.format(
        rubric=rubric,
        assignment_text=assignment_text,
        total_marks=total_marks
    )

    try:
        # Generate response using LangChain
        response = llm.invoke([HumanMessage(content=formatted_prompt)])

        # Parse the structured response
        parsed_result = parser.parse(response.content)

        return {
            "marks_obtained": parsed_result.marks_obtained,
            "total_marks": total_marks,
            "ai_feedback": parsed_result.feedback
        }

    except Exception as e:
        # Fallback to manual JSON parsing (similar to original approach)
        try:
            # Get raw response from LLM
            response = llm.invoke([HumanMessage(content=formatted_prompt)])
            result_text = response.content.strip()

            # Clean JSON response
            cleaned = clean_json(result_text)

            # Parse JSON
            result_json = json.loads(cleaned)
            marks = result_json.get("marks_obtained", 0)
            feedback = result_json.get("feedback", "")

            return {
                "marks_obtained": marks,
                "total_marks": total_marks,
                "ai_feedback": feedback
            }

        except Exception as fallback_error:
            # Final fallback if JSON parsing fails (same as original)
            return {
                "marks_obtained": 0,
                "total_marks": total_marks,
                "ai_feedback": f"Raw response: {result_text}\n\nError: {fallback_error}"
            }


def convert_file_to_base64(file_path: str) -> str:
    """
    Convert a PDF file to base64 string (useful for API transmission)
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Base64 encoded PDF data
    """
    try:
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        return base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to convert file to base64: {str(e)}")


def save_base64_to_file(base64_data: str, output_path: str) -> None:
    """
    Save base64 encoded PDF data to a file
    
    Args:
        base64_data: Base64 encoded PDF string
        output_path: Path where to save the PDF file
    """
    try:
        pdf_bytes = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
    except Exception as e:
        raise Exception(f"Failed to save base64 to file: {str(e)}")


def validate_pdf_blob(pdf_blob: Union[bytes, BinaryIO, str]) -> bool:
    """
    Validate if the provided BLOB data is a valid PDF
    
    Args:
        pdf_blob: PDF data as bytes, BinaryIO object, or base64 encoded string
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        # Handle different input types
        if isinstance(pdf_blob, str):
            try:
                pdf_bytes = base64.b64decode(pdf_blob)
            except Exception:
                return False
        elif isinstance(pdf_blob, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_blob)
        elif hasattr(pdf_blob, 'read'):
            pdf_bytes = pdf_blob.read()
            if hasattr(pdf_blob, 'seek'):
                pdf_blob.seek(0)
        else:
            return False
        
        # Check PDF magic number (PDF files start with %PDF)
        if pdf_bytes[:4] == b'%PDF':
            return True
        
        return False
        
    except Exception:
        return False


def demo_blob_usage():
    """
    Demonstrate how to use the BLOB functionality
    """
    questions = """ 
    Q: Explain Kirchoff's First Law and Second Law with Examples.
    """

    rubric_text = f"""
    - Questions: {questions}
    - Clarity of explanation (30 marks)
    - Correctness of answers (40 marks)  
    - Presentation & formatting (20 marks)
    - Originality (10 marks)
    - Ignore the Syntax/Grammar Mistakes If minor
    - Do not give marks for the questions that are not answered
    """

    # Example 1: Reading PDF file and converting to bytes (simulating BLOB)
    pdf_file_path = "Assignment-01-1.pdf"
    
    if os.path.exists(pdf_file_path):
        print("=== Testing BLOB functionality ===")
        
        # Read PDF file as bytes (simulating receiving BLOB data)
        with open(pdf_file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"PDF file size: {len(pdf_bytes)} bytes")
        
        # Grade using BLOB function
        result = grade_assignment_from_blob(pdf_bytes, rubric_text, total_marks=100)
        
        print("Grading Result from BLOB:")
        print(f"Marks: {result['marks_obtained']}/{result['total_marks']}")
        print(f"Feedback: {result['ai_feedback']}")
        
        # Example 2: Base64 encoded PDF
        print("\n=== Testing Base64 functionality ===")
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        print(f"Base64 string length: {len(pdf_base64)} characters")
        
        result_b64 = grade_assignment_from_blob(pdf_base64, rubric_text, total_marks=100)
        
        print("Grading Result from Base64:")
        print(f"Marks: {result_b64['marks_obtained']}/{result_b64['total_marks']}")
        print(f"Feedback: {result_b64['ai_feedback']}")
        
        # Example 3: BytesIO object
        print("\n=== Testing BytesIO functionality ===")
        pdf_stream = io.BytesIO(pdf_bytes)
        
        result_stream = grade_assignment_from_blob(pdf_stream, rubric_text, total_marks=100)
        
        print("Grading Result from BytesIO:")
        print(f"Marks: {result_stream['marks_obtained']}/{result_stream['total_marks']}")
        print(f"Feedback: {result_stream['ai_feedback']}")
        
    else:
        print(f"File not found: {pdf_file_path}")
        print("Please update the file path to test the grading system.")


if __name__ == "__main__":
    questions = """ 
    Q: Explain Kirchoff's First Law and Second Law with Examples.
    """

    rubric_text = f"""
    - Questions: {questions}
    - Clarity of explanation (30 marks)
    - Correctness of answers (40 marks)  
    - Presentation & formatting (20 marks)
    - Originality (10 marks)
    - Ignore the Syntax/Grammar Mistakes If minor
    - Do not give marks for the questions that are not answered
    """

    # Test traditional file-based approach
    pdf_file_path = "Assignment-01-1.pdf"

    print("=== Testing File-based approach ===")
    if os.path.exists(pdf_file_path):
        result = grade_assignment(pdf_file_path, rubric_text, total_marks=100)

        print("Grading Result from File:")
        print(f"Marks: {result['marks_obtained']}/{result['total_marks']}")
        print(f"Feedback: {result['ai_feedback']}")
        
        print("\n" + "="*50)
        
        # Test BLOB functionality
        demo_blob_usage()

    else:
        print(f"File not found: {pdf_file_path}")
        print("Please update the file path to test the grading system.")
        print("\nNote: The BLOB functionality will work with any PDF bytes data,")
        print("even without a physical file present.")