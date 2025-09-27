# Quiz Generator Feature

## Overview
The Quiz Generator is an AI-powered feature that creates interactive quizzes on Google Forms based on user-specified topics and difficulty levels. It integrates seamlessly with the existing EdRoom platform.

## Features
- **AI-Generated Questions**: Creates 20 multiple-choice questions using OpenAI
- **Google Forms Integration**: Automatically creates shareable Google Forms quizzes
- **Difficulty Levels**: Easy, Medium, and Hard difficulty options
- **Input Validation**: Validates topic length and difficulty selection
- **User-Friendly Interface**: Clean, intuitive UI with real-time feedback
- **No Database Storage**: As requested, quizzes are not saved to any database

## How to Use

### For Users
1. Open the EdRoom application
2. Click on the "Quiz Generator" tab
3. Enter your desired quiz topic (max 100 characters)
4. Select difficulty level (Easy, Medium, or Hard)
5. Click "Generate Quiz"
6. Wait for the AI to generate questions and create the Google Form
7. Use the provided link to access and share your quiz

### For Developers

#### Setup Requirements
1. **OpenAI API Key**: Required for question generation
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

2. **Google Forms API Credentials**: Required for creating Google Forms
   - Set up Google Cloud Project with Forms API enabled
   - Create OAuth 2.0 credentials
   - Download credentials.json to the quiz folder
   - Or set GOOGLE_APPLICATION_CREDENTIALS environment variable

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

#### Running the Application
1. **Start Backend**:
   ```bash
   python api_server.py
   ```

2. **Start Frontend**:
   ```bash
   cd ui
   npm install
   npm run dev
   ```

3. **Test the Quiz Agent**:
   ```bash
   python test_quiz_agent.py
   ```

## API Endpoints

### POST /api/quiz/generate
Generates a new quiz on Google Forms.

**Request Body**:
```json
{
  "topic": "World War II",
  "difficulty": "medium",
  "user_id": "optional_user_id"
}
```

**Response**:
```json
{
  "success": true,
  "quiz_info": {
    "form_id": "1a2b3c4d5e6f7g8h9i0j",
    "responder_url": "https://docs.google.com/forms/d/e/...",
    "title": "Auto Quiz: World War II (Medium)",
    "description": "Auto-generated quiz on World War II at medium difficulty level.",
    "topic": "World War II",
    "difficulty": "medium",
    "question_count": 20
  },
  "message": "Quiz successfully created! 20 questions generated.",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### GET /api/quiz/requirements
Returns the specifications and requirements for quiz generation.

**Response**:
```json
{
  "success": true,
  "requirements": {
    "required_fields": ["topic", "difficulty"],
    "topic_requirements": {
      "type": "string",
      "min_length": 1,
      "max_length": 100,
      "description": "The subject or topic for the quiz questions"
    },
    "difficulty_options": {
      "type": "enum",
      "values": ["easy", "medium", "hard"],
      "description": "The difficulty level for the quiz questions"
    },
    "output": {
      "question_count": 20,
      "question_type": "multiple_choice",
      "options_per_question": 4,
      "platform": "Google Forms"
    }
  }
}
```

## File Structure
```
├── Quiz_Generation_Agent.py          # Main quiz generation agent
├── api_server.py                     # API endpoints (updated)
├── test_quiz_agent.py               # Test script
├── ui/src/components/
│   └── QuizGenerator.jsx            # React UI component
├── ui/src/ChatApp.jsx               # Updated with tab navigation
└── quiz/                            # Existing quiz functionality
    ├── src/quiz_agent/
    │   ├── generator.py             # AI question generation
    │   ├── forms_api.py            # Google Forms integration
    │   └── config.py               # Configuration
    └── credentials.json            # Google API credentials
```

## Error Handling
- **Invalid Topic**: Empty or too long topics are rejected
- **Invalid Difficulty**: Only easy/medium/hard are accepted
- **API Failures**: Comprehensive error messages for debugging
- **Missing Credentials**: Clear warnings about missing API keys
- **Network Issues**: Graceful handling of connection problems

## Limitations
- Requires internet connection for AI generation and Google Forms API
- Limited to 20 questions per quiz (can be modified in config)
- Questions are in English (can be extended for multilingual support)
- Requires valid OpenAI and Google API credentials

## Troubleshooting

### Common Issues
1. **"No module named 'google_auth_oauthlib'"**
   - Run: `pip install google-auth-oauthlib`

2. **"OPENAI_API_KEY is not set"**
   - Add your OpenAI API key to the .env file

3. **"Google credentials not found"**
   - Set up Google Forms API credentials
   - Place credentials.json in the quiz folder

4. **"Failed to generate quiz questions"**
   - Check OpenAI API key validity
   - Verify internet connection
   - Try a different topic

### Testing
Run the test script to verify setup:
```bash
python test_quiz_agent.py
```

## Future Enhancements
- Support for different question types (true/false, short answer)
- Multilingual quiz generation
- Custom question count
- Quiz templates and themes
- Integration with learning management systems
- Analytics and performance tracking
