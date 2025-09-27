# Language Bridge & Content Moderation System

**Created by Claude**

A complete full-stack application with FastAPI backend and React frontend for language translation and content moderation using Google Cloud Translation API and OpenAI.

## 🌟 Features

### Backend (FastAPI)
- 🔍 **Automatic Language Detection**: Detects the language of input text with high accuracy and confidence scores
- 🌐 **Professional Translation**: Uses Google Cloud Translation API for high-quality translations
- 🛡️ **Content Moderation**: Uses OpenAI GPT-4o-mini for content safety analysis
- 🧠 **LangGraph Workflow**: Structured agent processing with clear steps and error handling
- 📊 **RESTful API**: Clean API endpoints with automatic documentation
- ⚡ **Smart Processing**: Skips translation if text is already in English
- 🔒 **CORS Enabled**: Proper CORS configuration for frontend integration
- 🌍 **100+ Languages**: Supports all languages available in Google Cloud Translation API

### Frontend (React)
- 🎨 **Modern UI**: Beautiful, responsive chatbot interface built with React and Tailwind CSS
- 💬 **Real-time Chat**: Interactive chat interface with typing indicators
- 📱 **Mobile Responsive**: Works seamlessly on desktop and mobile devices
- 🔍 **Visual Feedback**: Color-coded status indicators for translation and moderation
- 📋 **Expandable Details**: Click to view detailed translation and moderation information
- ⚡ **Fast Performance**: Built with Vite for optimal development and build performance

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    HTTP/REST API    ┌──────────────────┐
│   React Frontend│◄──────────────────►│  FastAPI Backend │
│   (Port 5173)   │                    │   (Port 8000)    │
└─────────────────┘                    └──────────────────┘
                                                │
                                                ▼
                                    ┌──────────────────────┐
                                    │   LangGraph Workflow │
                                    │                      │
                                    │  1. Input Validation │
                                    │  2. Language Detection│
                                    │  3. Translation      │
                                    │  4. Content Moderation│
                                    │  5. Final Decision   │
                                    └──────────────────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                            ┌──────────────┐    ┌──────────────────┐
                            │ Google Cloud │    │     OpenAI       │
                            │ Translation  │    │   GPT-4o-mini    │
                            │     API      │    │ Content Moderation│
                            └──────────────┘    └──────────────────┘
```

### Backend Workflow
1. **Input Validation**: Validates the input text (length, content)
2. **Language Detection**: Detects the language using Google Cloud Translation API
3. **Translation**: Translates to English (if needed)
4. **Content Moderation**: Analyzes translated content for inappropriate material
5. **Final Decision**: Returns approval status with comprehensive details

## 📋 Prerequisites

### Google Cloud Setup

1. **Google Cloud Account**: You need a Google Cloud account
2. **Project**: Create or select a Google Cloud project
3. **Translation API**: Enable the Cloud Translation API
4. **Service Account**: Create a service account with Translation API permissions
5. **Credentials**: Download the JSON key file

### Detailed Setup Instructions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Cloud Translation API:
   - Go to APIs & Services > Library
   - Search for "Cloud Translation API"
   - Click "Enable"
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Give it a name and description
   - Grant "Cloud Translation API User" role
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format and download

## 🚀 Quick Start

### Option 1: Start Both Backend and Frontend (Recommended)
```bash
python start_server.py both
```

### Option 2: Start Individually

**Backend Only:**
```bash
python start_backend.py
# or
python api_server.py
```

**Frontend Only:**
```bash
python start_frontend.py
# or
cd ui && npm run dev
```

### Option 3: Interactive Menu
```bash
python start_server.py
```

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd language-bridge-system
```

### 2. Backend Setup (Python)
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (Node.js)
```bash
# Install Node.js dependencies
cd ui
npm install
cd ..
```

### 4. Environment Configuration

Create a `.env` file in the project root:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
OPENAI_API_KEY=your_openai_api_key_here
```

**Google Cloud Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project and enable Translation API
3. Create a service account with "Cloud Translation API User" role
4. Download the JSON key file

**OpenAI Setup:**
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an API key
3. Add it to your `.env` file

## 📦 Dependencies

- `langgraph>=0.0.40` - For building the agent workflow
- `langchain>=0.1.0` - LangChain core functionality
- `langchain-core>=0.1.0` - LangChain core components
- `google-cloud-translate>=3.12.0` - Official Google Cloud Translation API
- `typing-extensions>=4.5.0` - Type hints support
- `colorlog>=6.7.0` - Enhanced logging (optional)

## 💻 Usage

### Web Interface (Recommended)

1. Start both servers:
   ```bash
   python start_server.py both
   ```

2. Open your browser and go to:
   - **Frontend UI**: http://localhost:5173
   - **API Documentation**: http://localhost:8000/docs

3. Use the chatbot interface to:
   - Type messages in any language
   - See real-time translation and moderation
   - View detailed processing information

### API Endpoints

#### Chat Endpoint
```bash
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Bonjour, comment allez-vous?",
  "user_id": "user123",
  "session_id": "session456"
}
```

#### Direct Processing Endpoint
```bash
POST http://localhost:8000/api/process
Content-Type: application/json

{
  "text": "Hola, ¿cómo estás?",
  "user_id": "user123"
}
```

### Programmatic Usage

```python
import requests

# Using the chat endpoint
response = requests.post("http://localhost:8000/api/chat", json={
    "message": "Bonjour, comment allez-vous?",
    "user_id": "web-user"
})

result = response.json()
if result["success"]:
    print(f"Bot Response: {result['bot_response']}")
    print(f"Final Approved: {result['final_approved']}")
```

### Command Line Usage

```bash
# Interactive translation and moderation
python Language_Bridge_Agent.py

# Backend API server
python api_server.py

# Frontend development server
cd ui && npm run dev
```

### Advanced Usage with Custom Credentials

```python
from Language_Bridge_Agent import LanguageBridgeAgent

# Initialize with custom credentials path
agent = LanguageBridgeAgent(credentials_path="path/to/credentials.json")

# Process multiple texts
texts = [
    "Hello, how are you?",
    "Hola, ¿cómo estás?",
    "こんにちは、元気ですか？"
]

for text in texts:
    result = agent.process_text(text)
    print(f"Input: {text}")
    print(f"Translation: {result['translated_text']}")
    print("-" * 30)

# Get supported languages
supported_languages = agent.get_supported_languages()
print(f"Supported languages: {len(supported_languages)}")
```

## 📊 API Response Format

The agent returns a comprehensive dictionary:

```python
{
    "success": bool,                    # Whether processing was successful
    "input_text": str,                  # Original input text
    "detected_language": str,           # Full language name (e.g., "French")
    "detected_language_code": str,      # Language code (e.g., "fr")
    "confidence": float,                # Detection confidence (0.0 to 1.0)
    "translated_text": str,             # Translated text in English
    "is_english": bool,                 # Whether input was already English
    "error": str,                       # Error message (if any)
    "processing_step": str,             # Last completed processing step
    "metadata": dict                    # Additional processing metadata
}
```

## 🌍 Supported Languages

The agent supports 100+ languages through Google Cloud Translation API, including:

- **European Languages**: English, French, Spanish, German, Italian, Portuguese, Dutch, Russian, Polish, etc.
- **Asian Languages**: Chinese (Simplified/Traditional), Japanese, Korean, Hindi, Arabic, Thai, Vietnamese, etc.
- **African Languages**: Swahili, Yoruba, Zulu, Afrikaans, etc.
- **Other Languages**: Hebrew, Turkish, Greek, Czech, Hungarian, and many more

Use the `get_supported_languages()` method to get the complete list.

## 📝 Examples

### Example 1: French Text
```python
Input: "Bonjour, comment allez-vous?"
Output: {
    "success": True,
    "detected_language": "French",
    "detected_language_code": "fr",
    "confidence": 0.99,
    "translated_text": "Hello, how are you?",
    "is_english": False
}
```

### Example 2: Already English
```python
Input: "Hello, how are you?"
Output: {
    "success": True,
    "detected_language": "English",
    "detected_language_code": "en",
    "confidence": 0.99,
    "translated_text": "Hello, how are you?",
    "is_english": True
}
```

### Example 3: Japanese Text
```python
Input: "こんにちは、元気ですか？"
Output: {
    "success": True,
    "detected_language": "Japanese",
    "detected_language_code": "ja",
    "confidence": 1.0,
    "translated_text": "Hello, how are you?",
    "is_english": False
}
```

## 🛠️ Error Handling

The agent includes comprehensive error handling for:

- Empty or invalid input text
- Text exceeding length limits (30,000 characters)
- Google Cloud API authentication issues
- Network connectivity problems
- API rate limiting
- Invalid language detection results
- Translation failures
- Graph execution errors

## 📋 Logging

The agent uses Python's logging module with detailed information about:

- Processing steps with emojis for easy reading
- Language detection results with confidence scores
- Translation progress and results
- Error conditions with detailed messages
- Performance and timing information

## 💰 Cost Considerations

Google Cloud Translation API is a paid service:

- **Language Detection**: $20 per 1M characters
- **Translation**: $20 per 1M characters
- **Free Tier**: 500,000 characters per month

Monitor your usage in the Google Cloud Console to avoid unexpected charges.

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: Failed to initialize Google Cloud Translation client
   ```
   **Solution**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set or pass `credentials_path`

2. **API Not Enabled**
   ```
   Error: Cloud Translation API has not been used
   ```
   **Solution**: Enable the Cloud Translation API in Google Cloud Console

3. **Permission Denied**
   ```
   Error: The caller does not have permission
   ```
   **Solution**: Ensure your service account has "Cloud Translation API User" role

4. **Network Issues**
   ```
   Error: Failed to establish a new connection
   ```
   **Solution**: Check internet connection and firewall settings

### Getting Help

1. Check the error messages in the console
2. Enable debug logging for more detailed information
3. Verify Google Cloud setup and credentials
4. Test with simple text first
5. Check Google Cloud Console for API usage and errors

## 🚀 Performance Tips

1. **Batch Processing**: Process multiple texts in sequence to amortize setup costs
2. **Caching**: Consider caching results for frequently translated texts
3. **Text Length**: Shorter texts generally have faster processing times
4. **Error Handling**: Implement retry logic for transient network errors

## 🔮 Future Enhancements

- Support for multiple target languages
- Batch processing capabilities
- Result caching for improved performance
- Integration with other translation services
- Web API interface
- GUI interface
- Advanced language detection options
- Custom translation models

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. Adding support for more translation services
2. Implementing caching mechanisms
3. Adding more comprehensive tests
4. Optimizing performance
5. Adding new features and capabilities

## 📚 Documentation

- [Google Cloud Translation API Documentation](https://cloud.google.com/translate/docs)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Documentation](https://python.langchain.com/)

## 🙏 Acknowledgments

- **Google Cloud Translation API** for providing high-quality translation services
- **LangGraph** for the powerful workflow framework
- **LangChain** for the foundational AI agent capabilities

---

**Created by Claude** - An AI assistant focused on creating high-quality, production-ready code solutions.
