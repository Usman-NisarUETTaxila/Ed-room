#!/usr/bin/env python3
"""
Final verification script for Quiz Generation System
Tests the complete end-to-end functionality
"""

import json
from Quiz_Generation_Agent import create_quiz, get_quiz_requirements

def test_complete_quiz_flow():
    """Test the complete quiz generation flow"""
    print("🎯 Testing Complete Quiz Generation Flow")
    print("=" * 50)
    
    # Test 1: Get requirements
    print("📋 Step 1: Getting quiz requirements...")
    try:
        requirements = get_quiz_requirements()
        print("✅ Requirements retrieved successfully")
        print(f"   - Difficulties: {requirements['difficulty_options']['values']}")
        print(f"   - Question count: {requirements['output']['question_count']}")
    except Exception as e:
        print(f"❌ Failed to get requirements: {e}")
        return False
    
    # Test 2: Generate quiz
    print("\n🎲 Step 2: Generating quiz...")
    try:
        result = create_quiz("Basic Computer Science", "medium")
        
        if result["success"]:
            quiz_info = result["quiz_info"]
            print("✅ Quiz generated successfully!")
            print(f"   - Form ID: {quiz_info['form_id']}")
            print(f"   - Title: {quiz_info['title']}")
            print(f"   - Questions: {quiz_info['question_count']}")
            print(f"   - URL: {quiz_info['responder_url']}")
            
            # Verify the URL is accessible
            if quiz_info['responder_url'].startswith('https://docs.google.com/forms'):
                print("✅ Google Forms URL format is correct")
            else:
                print("⚠️ Unexpected URL format")
                
            return True
        else:
            print(f"❌ Quiz generation failed: {result.get('error', 'Unknown error')}")
            if result.get('details'):
                for detail in result['details']:
                    print(f"   - {detail}")
            return False
            
    except Exception as e:
        print(f"❌ Quiz generation exception: {e}")
        return False

def test_input_validation():
    """Test input validation"""
    print("\n🔍 Step 3: Testing input validation...")
    
    test_cases = [
        ("", "easy", False, "Empty topic"),
        ("Valid Topic", "invalid", False, "Invalid difficulty"),
        ("A" * 101, "easy", False, "Topic too long"),
        ("Valid Topic", "easy", True, "Valid inputs"),
    ]
    
    for topic, difficulty, should_pass, description in test_cases:
        try:
            result = create_quiz(topic, difficulty)
            success = result["success"]
            
            if should_pass and success:
                print(f"✅ {description}: Passed as expected")
            elif not should_pass and not success:
                print(f"✅ {description}: Failed as expected")
            else:
                print(f"❌ {description}: Unexpected result (success={success})")
                
        except Exception as e:
            if should_pass:
                print(f"❌ {description}: Unexpected exception: {e}")
            else:
                print(f"✅ {description}: Exception as expected")

if __name__ == "__main__":
    print("🧪 Quiz Generation System Verification")
    print("=" * 60)
    
    # Run complete flow test
    flow_success = test_complete_quiz_flow()
    
    # Run validation tests
    test_input_validation()
    
    print("\n" + "=" * 60)
    if flow_success:
        print("🎉 VERIFICATION COMPLETE: Quiz Generation System is working!")
        print("\n📝 Ready to use:")
        print("   1. Start backend: python api_server.py")
        print("   2. Start frontend: cd ui && npm run dev")
        print("   3. Navigate to Quiz Generator tab")
        print("   4. Enter topic and difficulty")
        print("   5. Generate and share your quiz!")
    else:
        print("❌ VERIFICATION FAILED: Please check the setup")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify OpenAI API key is set")
        print("   2. Check Google Forms API credentials")
        print("   3. Ensure internet connection")
        print("   4. Review error messages above")
