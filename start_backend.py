#!/usr/bin/env python3
"""
Backend Startup Script for Language Bridge & Content Moderation API
Created by Claude
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    """Check if required environment variables are set"""
    print("🔧 Checking backend environment...")
    
    missing_vars = []
    
    # Check for Google Cloud credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n📋 Setup Instructions:")
        print("1. Create a .env file in the project root directory")
        print("2. Add the following variables:")
        print("   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    print("✅ Backend environment variables are set")
    return True

def check_dependencies():
    """Check if required Python dependencies are installed"""
    print("📦 Checking Python dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'langchain-openai',
        'langgraph',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("\n📋 Install missing packages:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All Python dependencies are installed")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI Backend Server...")
    print("=" * 50)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend server: {e}")
        return False
    except FileNotFoundError:
        print("❌ uvicorn not found. Please install it with: pip install uvicorn[standard]")
        return False
    
    return True

def main():
    """Main function"""
    print("🌍🛡️ Language Bridge & Content Moderation - Backend")
    print("Created by Claude")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("api_server.py").exists():
        print("❌ api_server.py not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n⚠️ Environment setup incomplete. Please fix the issues above and try again.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️ Dependencies missing. Please install them and try again.")
        sys.exit(1)
    
    # Start backend server
    print("\n🎯 All checks passed! Starting backend server...")
    start_backend()

if __name__ == "__main__":
    main()
