#!/usr/bin/env python3
"""
Test script for Arabic language support
"""

import os
import logging
from Language_Bridge_Agent import process_with_moderation, translate_response_to_user_language

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_arabic_input():
    """Test Arabic input processing"""
    
    # Test Arabic text
    arabic_text = "اشرح لي الذكاء الاصطناعي"  # "Explain artificial intelligence to me"
    
    print("🧪 Testing Arabic Language Support")
    print("=" * 50)
    print(f"Input text: {arabic_text}")
    print()
    
    # Test translation and moderation
    print("Step 1: Testing input processing...")
    result = process_with_moderation(arabic_text)
    
    print(f"Success: {result.get('success', False)}")
    print(f"Original language: {result.get('original_language', 'Unknown')}")
    print(f"Language code: {result.get('original_language_code', 'Unknown')}")
    print(f"Translated text: {result.get('translated_text', 'None')}")
    print(f"Is English: {result.get('is_english', False)}")
    print(f"Final approved: {result.get('final_approved', False)}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
        return
    
    print()
    
    # Test response translation back to Arabic
    if result.get('success') and result.get('original_language_code'):
        print("Step 2: Testing response translation...")
        
        # Sample English response
        english_response = "🎓 **Here's what I can tell you about artificial intelligence:**\n\nArtificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior."
        
        print(f"English response: {english_response[:100]}...")
        print()
        
        translation_result = translate_response_to_user_language(
            response_text=english_response,
            target_language_code=result['original_language_code']
        )
        
        print(f"Translation success: {translation_result.get('success', False)}")
        print(f"Translated response: {translation_result.get('translated_text', 'None')}")
        
        if translation_result.get('error'):
            print(f"Translation error: {translation_result['error']}")

def test_simple_arabic():
    """Test simple Arabic translation"""
    print("\n🔍 Testing Simple Arabic Translation")
    print("=" * 50)
    
    from Language_Bridge_Agent import LanguageBridgeAgent
    
    try:
        agent = LanguageBridgeAgent()
        
        # Test simple Arabic text
        arabic_text = "مرحبا"  # "Hello"
        print(f"Testing: {arabic_text}")
        
        # Test language detection
        result = agent.process_text(arabic_text)
        print(f"Detection result: {result}")
        
        # Test translation to Arabic
        english_text = "Hello, how are you?"
        translation_result = agent.translate_to_language(
            text=english_text,
            target_language_code='ar',
            source_language_code='en'
        )
        print(f"Translation result: {translation_result}")
        
    except Exception as e:
        print(f"Error in simple test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check environment
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set!")
        print("Please set your Google Cloud credentials.")
        exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not set - some features may not work")
    
    print("🌍 Arabic Language Support Test")
    print("Testing Arabic input and output translation...")
    print()
    
    try:
        test_arabic_input()
        test_simple_arabic()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test completed!")
