#!/usr/bin/env python3
"""
Test OpenAI API connection for quiz generation
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test if OpenAI API is accessible"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            print("   Please add OPENAI_API_KEY to your .env file")
            return False
        
        print(f"✅ OPENAI_API_KEY found (length: {len(api_key)})")
        
        # Test API connection with a simple request
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing OpenAI API connection...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, API test successful!'"}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API test successful: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_quiz_generation_simple():
    """Test a simple quiz generation without Google Forms"""
    try:
        import sys
        from pathlib import Path
        
        # Add quiz path
        quiz_path = Path(__file__).parent / "quiz"
        sys.path.insert(0, str(quiz_path))
        
        from src.quiz_agent.generator import generate_mcqs
        
        print("🔄 Testing quiz question generation...")
        
        # Generate just 2 questions for testing
        mcqs = generate_mcqs("Basic Math", "easy")
        
        if mcqs and len(mcqs) > 0:
            print(f"✅ Successfully generated {len(mcqs)} questions")
            print(f"   Sample question: {mcqs[0].question}")
            return True
        else:
            print("❌ No questions generated")
            return False
            
    except Exception as e:
        print(f"❌ Quiz generation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenAI Connection and Quiz Generation")
    print("=" * 50)
    
    # Test OpenAI connection first
    openai_ok = test_openai_connection()
    
    if openai_ok:
        print("\n" + "=" * 50)
        # Test quiz generation if OpenAI works
        quiz_ok = test_quiz_generation_simple()
        
        if quiz_ok:
            print("\n🎉 All tests passed! Quiz generation should work now.")
        else:
            print("\n⚠️ OpenAI works but quiz generation failed. Check the generator code.")
    else:
        print("\n⚠️ OpenAI API connection failed. Please check your API key.")
        print("\nTo fix:")
        print("1. Make sure you have a valid OpenAI API key")
        print("2. Add it to your .env file: OPENAI_API_KEY=your_key_here")
        print("3. Restart the application")
