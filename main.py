"""
Main script to demonstrate the Language Bridge Agent, Content Moderation Agent, and Integrated Agent
Created by Claude
"""

import os
import sys
from Language_Bridge_Agent import create_language_bridge_agent
from Content_Moderation_Agent import create_content_moderation_agent
import json

def setup_google_cloud_credentials():
    """
    Helper function to set up Google Cloud credentials
    """
    print("🔧 Google Cloud Translation API Setup")
    print("=" * 50)
    
    # Check if credentials are already set
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("✅ GOOGLE_APPLICATION_CREDENTIALS environment variable is set")
        return True
    
    print("⚠️  Google Cloud credentials not found!")
    print("\n📋 Setup Instructions:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Cloud Translation API")
    print("4. Create a service account:")
    print("   - Go to IAM & Admin > Service Accounts")
    print("   - Click 'Create Service Account'")
    print("   - Give it a name and description")
    print("   - Grant 'Cloud Translation API User' role")
    print("5. Create and download a JSON key file")
    print("6. Set the environment variable:")
    print("   Windows: set GOOGLE_APPLICATION_CREDENTIALS=path\\to\\your\\key.json")
    print("   Linux/Mac: export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/key.json")
    
    # Ask user if they want to provide credentials path
    print("\n" + "=" * 50)
    credentials_path = input("Enter path to your Google Cloud credentials JSON file (or press Enter to skip): ").strip()
    
    if credentials_path and os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print(f"✅ Credentials set to: {credentials_path}")
        return True
    elif credentials_path:
        print(f"❌ File not found: {credentials_path}")
        return False
    
    return False

def interactive_demo():
    """Interactive demonstration of the Language Bridge Agent"""
    print("\n🌍 Language Bridge Agent - Interactive Demo")
    print("=" * 60)
    print("This agent detects language and translates text to English using Google Cloud Translation API")
    print("Type 'quit', 'exit', or 'q' to stop the program")
    print("Type 'help' for available commands")
    print("Type 'languages' to see supported languages\n")
    
    # Create the agent
    try:
        agent = create_language_bridge_agent()
        print("✅ Language Bridge Agent initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("Enter text to translate: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("\n📋 Available Commands:")
                print("  - Enter any text to detect language and translate")
                print("  - 'languages' - Show supported languages")
                print("  - 'quit' or 'exit' - Exit the program")
                print("  - 'help' - Show this help message\n")
                continue
            elif user_input.lower() == 'languages':
                print("\n🌐 Getting supported languages...")
                try:
                    supported_langs = agent.get_supported_languages()
                    print(f"✅ Google Cloud Translation API supports {len(supported_langs)} languages:")
                    
                    # Show first 20 languages as example
                    for i, (code, name) in enumerate(list(supported_langs.items())[:20]):
                        print(f"  {code}: {name}")
                    
                    if len(supported_langs) > 20:
                        print(f"  ... and {len(supported_langs) - 20} more languages")
                    print()
                except Exception as e:
                    print(f"❌ Failed to get supported languages: {e}\n")
                continue
            elif not user_input:
                print("⚠️  Please enter some text to translate.\n")
                continue
            
            print(f"\n🔄 Processing: '{user_input}'")
            print("-" * 40)
            
            # Process the text
            result = agent.process_text(user_input)
            
            # Display results
            if result["success"]:
                print(f"🔍 Detected Language: {result['detected_language']} ({result['detected_language_code']})")
                print(f"📊 Confidence: {result['confidence']:.1%}")
                
                if result['is_english']:
                    print("ℹ️  Text is already in English")
                    print(f"📝 Original Text: {result['translated_text']}")
                else:
                    print(f"🌐 Translation: {result['translated_text']}")
                
                # Show metadata if available
                if result.get('metadata'):
                    print(f"⚙️  Processing Step: {result['processing_step']}")
                
            else:
                print(f"❌ Error: {result['error']}")
            
            print("\n" + "=" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}\n")

def batch_test_demo():
    """Batch testing demonstration with various languages"""
    print("\n🧪 Language Bridge Agent - Batch Test Demo")
    print("=" * 60)
    
    # Create agent
    try:
        agent = create_language_bridge_agent()
        print("✅ Agent initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Comprehensive test cases
    test_cases = [
        # English (should skip translation)
        ("Hello, how are you today?", "English"),
        ("The quick brown fox jumps over the lazy dog.", "English"),
        
        # European languages
        ("Bonjour, comment allez-vous aujourd'hui?", "French"),
        ("Hola, ¿cómo estás hoy?", "Spanish"),
        ("Guten Tag, wie geht es Ihnen heute?", "German"),
        ("Ciao, come stai oggi?", "Italian"),
        ("Olá, como você está hoje?", "Portuguese"),
        ("Привет, как дела сегодня?", "Russian"),
        
        # Asian languages
        ("こんにちは、今日はいかがですか？", "Japanese"),
        ("你好，你今天怎么样？", "Chinese (Simplified)"),
        ("안녕하세요, 오늘 어떻게 지내세요?", "Korean"),
        ("नमस्ते, आज आप कैसे हैं?", "Hindi"),
        
        # Middle Eastern and African languages
        ("مرحبا، كيف حالك اليوم؟", "Arabic"),
        ("שלום, איך אתה היום?", "Hebrew"),
        
        # Edge cases
        ("", "Empty input (should fail)"),
        ("Hi!", "Very short text"),
        ("123456789", "Numbers only"),
        ("Hello! 你好! Bonjour!", "Mixed languages"),
    ]
    
    print(f"Running {len(test_cases)} test cases...\n")
    
    results = []
    successful_tests = 0
    
    for i, (text, description) in enumerate(test_cases, 1):
        print(f"Test {i:2d}: {description}")
        print(f"Input: '{text}'")
        
        try:
            result = agent.process_text(text)
            
            if result["success"]:
                print(f"✅ Detected: {result['detected_language']} ({result['detected_language_code']})")
                print(f"✅ Confidence: {result['confidence']:.1%}")
                print(f"✅ Translation: '{result['translated_text']}'")
                if result['is_english']:
                    print("ℹ️  No translation needed (already English)")
                
                successful_tests += 1
                results.append({
                    "test_case": i,
                    "input": text,
                    "description": description,
                    "detected_language": result['detected_language'],
                    "detected_code": result['detected_language_code'],
                    "confidence": result['confidence'],
                    "translation": result['translated_text'],
                    "is_english": result['is_english'],
                    "success": True
                })
            else:
                print(f"❌ Error: {result['error']}")
                results.append({
                    "test_case": i,
                    "input": text,
                    "description": description,
                    "error": result['error'],
                    "success": False
                })
        
        except Exception as e:
            print(f"💥 Exception: {e}")
            results.append({
                "test_case": i,
                "input": text,
                "description": description,
                "exception": str(e),
                "success": False
            })
        
        print("-" * 60)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"✅ Successful tests: {successful_tests}/{len(test_cases)}")
    print(f"❌ Failed tests: {len(test_cases) - successful_tests}/{len(test_cases)}")
    print(f"📈 Success rate: {(successful_tests/len(test_cases)*100):.1f}%")
    
    return results

def content_moderation_demo():
    """Demonstration of the Content Moderation Agent"""
    print("\n🛡️ Content Moderation Agent - Demo")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not found!")
        print("Please set your OpenAI API key in the .env file or environment variables.")
        return
    
    try:
        agent = create_content_moderation_agent()
        print("✅ Content Moderation Agent initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize Content Moderation Agent: {e}")
        return
    
    # Test cases for content moderation
    test_cases = [
        ("Hello, how are you today?", "Clean, friendly text"),
        ("This is a great product! I highly recommend it.", "Positive review"),
        ("I hate this stupid thing!", "Mild profanity/negative sentiment"),
        ("The weather is nice today.", "Neutral, safe content"),
        ("", "Empty input (should fail)"),
    ]
    
    print(f"Running {len(test_cases)} content moderation test cases...\n")
    
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
        
        print("-" * 60)



def main():
    """Main function to run the demonstration"""
    print("🌍🛡️ Language Bridge + Content Moderation Agents - Claude Edition")
    print("Created by Claude")
    print("=" * 90)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--translation" or sys.argv[1] == "-t":
            # Check for Google Cloud credentials
            if not setup_google_cloud_credentials():
                print("\n⚠️  Warning: Google Cloud credentials not configured.")
                choice = input("\nDo you want to continue anyway? (y/N): ").strip().lower()
                if choice not in ['y', 'yes']:
                    return
            batch_test_demo()
        elif sys.argv[1] == "--moderation" or sys.argv[1] == "-m":
            content_moderation_demo()
        elif sys.argv[1] == "--integrated" or sys.argv[1] == "-i":
            integrated_agent_demo()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("\n📋 Usage:")
            print("  python main.py                    - Run interactive translation demo")
            print("  python main.py --translation      - Run translation batch test")
            print("  python main.py --moderation       - Run content moderation demo")
            print("  python main.py --integrated       - Run integrated agent demo")
            print("  python main.py --help             - Show this help message")
            print("\n🔧 Setup Requirements:")
            print("  - Google Cloud Translation API credentials for translation")
            print("  - OpenAI API key for content moderation")
            print("  - Both required for integrated agent")
        else:
            print(f"❌ Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Run interactive translation demo by default
        if not setup_google_cloud_credentials():
            print("\n⚠️  Warning: Google Cloud credentials not configured.")
            choice = input("\nDo you want to continue anyway? (y/N): ").strip().lower()
            if choice not in ['y', 'yes']:
                print("👋 Exiting. Please set up Google Cloud credentials and try again.")
                return
        interactive_demo()

if __name__ == "__main__":
    main()