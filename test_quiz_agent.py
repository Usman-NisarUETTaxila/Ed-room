#!/usr/bin/env python3
"""
Test script for Quiz Generation Agent
Tests the quiz generation functionality without requiring the full web interface
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_quiz_agent_import():
    """Test if we can import the quiz agent"""
    try:
        from Quiz_Generation_Agent import create_quiz, get_quiz_requirements
        print("✅ Successfully imported Quiz Generation Agent")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Quiz Generation Agent: {e}")
        return False

def test_quiz_requirements():
    """Test getting quiz requirements"""
    try:
        from Quiz_Generation_Agent import get_quiz_requirements
        requirements = get_quiz_requirements()
        print("✅ Successfully retrieved quiz requirements:")
        print(f"   - Required fields: {requirements['required_fields']}")
        print(f"   - Difficulty options: {requirements['difficulty_options']['values']}")
        print(f"   - Output: {requirements['output']['question_count']} {requirements['output']['question_type']} questions")
        return True
    except Exception as e:
        print(f"❌ Failed to get quiz requirements: {e}")
        return False

def test_input_validation():
    """Test input validation without actually generating a quiz"""
    try:
        from Quiz_Generation_Agent import quiz_agent
        
        # Test valid inputs
        valid_result = quiz_agent.validate_inputs("Python Programming", "medium")
        print(f"✅ Valid input validation: {valid_result}")
        
        # Test invalid inputs
        invalid_result = quiz_agent.validate_inputs("", "invalid")
        print(f"✅ Invalid input validation: {invalid_result}")
        
        return True
    except Exception as e:
        print(f"❌ Failed input validation test: {e}")
        return False

def test_environment_setup():
    """Test if required environment variables and files are present"""
    print("\n🔍 Checking environment setup:")
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("⚠️  OPENAI_API_KEY is not set (required for quiz generation)")
    
    # Check for Google credentials
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds_file = Path("quiz/credentials.json")
    
    if google_creds:
        print("✅ GOOGLE_APPLICATION_CREDENTIALS is set")
    elif creds_file.exists():
        print("✅ Google credentials file found at quiz/credentials.json")
    else:
        print("⚠️  Google credentials not found (required for Google Forms integration)")
    
    # Check quiz folder structure
    quiz_folder = Path("quiz")
    if quiz_folder.exists():
        print("✅ Quiz folder exists")
        
        required_files = [
            "quiz/src/quiz_agent/__init__.py",
            "quiz/src/quiz_agent/generator.py",
            "quiz/src/quiz_agent/forms_api.py",
            "quiz/src/quiz_agent/config.py"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
    else:
        print("❌ Quiz folder not found")

def main():
    """Run all tests"""
    print("🧪 Testing Quiz Generation Agent")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_quiz_agent_import),
        ("Requirements Test", test_quiz_requirements),
        ("Validation Test", test_input_validation),
        ("Environment Test", test_environment_setup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Quiz Generation Agent is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Ensure OPENAI_API_KEY is set in your .env file")
        print("   2. Set up Google Forms API credentials")
        print("   3. Start the backend server: python api_server.py")
        print("   4. Start the frontend: cd ui && npm run dev")
    else:
        print("\n⚠️  Some tests failed. Please check the setup before using the quiz generator.")

if __name__ == "__main__":
    main()
