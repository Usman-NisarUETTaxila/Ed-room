import os
import sys
from openai import OpenAI
from typing import Optional
import json



# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass

class EducationalAIAgent:
    """
    An AI agent that provides educational explanations on any topic using OpenAI's ChatGPT API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Educational AI Agent.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will look for OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.conversation_history = []
        
        # System prompt for educational explanations
        self.system_prompt = """You are an expert educational AI assistant. Your role is to provide clear, comprehensive, and engaging explanations on any topic the user asks about. 

Guidelines for your responses:
1. Provide accurate and well-structured explanations
2. Use simple language when possible, but don't oversimplify complex concepts
3. Include examples when helpful
4. Break down complex topics into digestible parts
5. Encourage further learning by suggesting related topics or resources
6. If the topic is very broad, ask for clarification or provide an overview with key subtopics
7. Always maintain an encouraging and supportive tone
8. If you're unsure about something, acknowledge it and provide the best information you can

Remember: Your goal is to help users learn and understand, not just provide answers."""

    def get_explanation(self, user_input: str, include_history: bool = True) -> str:
        """
        Get an educational explanation for the user's input.
        
        Args:
            user_input (str): The topic or question the user wants explained
            include_history (bool): Whether to include conversation history for context
            
        Returns:
            str: The AI's explanation response
        """
        try:
            # Prepare messages for the API call
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if requested
            if include_history and self.conversation_history:
                messages.extend(self.conversation_history)
            
            # Add the current user input
            messages.append({"role": "user", "content": user_input})
            
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",  # You can change to "gpt-4" for better responses
                messages=messages,
                max_tokens=1500,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extract the response
            explanation = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": explanation})
            
            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return explanation
            
        except Exception as e:
            return f"Sorry, I encountered an error while generating the explanation: {str(e)}"
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        print("Conversation history cleared!")
    
    def save_conversation(self, filename: str = "conversation_history.json"):
        """
        Save the current conversation to a JSON file.
        
        Args:
            filename (str): Name of the file to save the conversation
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            print(f"Conversation saved to {filename}")
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")
    
    def load_conversation(self, filename: str = "conversation_history.json"):
        """
        Load a conversation from a JSON file.
        
        Args:
            filename (str): Name of the file to load the conversation from
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
            print(f"Conversation loaded from {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found.")
        except Exception as e:
            print(f"Error loading conversation: {str(e)}")

def main():
    """
    Main function to run the Educational AI Agent interactively.
    """
    print("🎓 Educational AI Agent")
    print("=" * 50)
    print("Welcome! I'm here to help explain any topic you're curious about.")
    print("Type 'quit' to exit, 'clear' to clear history, 'save' to save conversation, or 'load' to load a previous conversation.")
    print("=" * 50)
    
    try:
        # Initialize the AI agent
        agent = EducationalAIAgent()
        
        while True:
            # Get user input
            user_input = input("\n🤔 What would you like me to explain? ").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for learning with me! Goodbye!")
                break
            elif user_input.lower() == 'clear':
                agent.clear_history()
                continue
            elif user_input.lower() == 'save':
                filename = input("Enter filename (or press Enter for default): ").strip()
                if not filename:
                    filename = "conversation_history.json"
                agent.save_conversation(filename)
                continue
            elif user_input.lower() == 'load':
                filename = input("Enter filename (or press Enter for default): ").strip()
                if not filename:
                    filename = "conversation_history.json"
                agent.load_conversation(filename)
                continue
            elif not user_input:
                print("Please enter a topic or question you'd like me to explain.")
                continue
            
            # Get and display explanation
            print("\n🤖 Let me explain that for you...\n")
            explanation = agent.get_explanation(user_input)
            print(f"📚 {explanation}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for learning with me! Goodbye!")
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nTo fix this:")
        print("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Set it as an environment variable: set OPENAI_API_KEY=your_api_key_here")
        print("3. Or pass it directly when creating the EducationalAIAgent")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()