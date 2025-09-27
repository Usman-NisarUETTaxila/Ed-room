# AI Quiz Agent for Google Forms

This tool generates a 20-question multiple-choice quiz for a given topic and difficulty using an LLM, creates it as a Google Form quiz (with correct answers and points), and can fetch responses and compute scores.

## Features
- 20 MCQs per quiz, 4 options each, with correct answers and explanations.
- Creates a Google Form set as a quiz, with points and correct answers.
- CLI to create quizzes and grade responses.

## Prerequisites
- Python 3.10+
- A Google account
- Google Cloud project with the Forms API enabled
- OAuth Client (Desktop) credentials JSON
- An OpenAI API key

## Setup
1. Clone or open this project folder: `c:\quiz`
2. Create and activate a virtual environment (recommended):
   - Windows PowerShell:
     ```powershell
     py -3 -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill values:
   - `OPENAI_API_KEY` and optionally `OPENAI_MODEL`
   - `GOOGLE_CREDENTIALS_FILE` path to your downloaded OAuth client JSON, e.g. `credentials.json` in the project root
   - `GOOGLE_TOKEN_FILE` default `token.json`

5. Enable Google Forms API:
   - Go to Google Cloud Console > APIs & Services > Library > enable "Google Forms API".
   - Go to Credentials > Create Credentials > OAuth client ID > Application type: Desktop app.
   - Download the JSON and save it as `credentials.json` in the project root or update `GOOGLE_CREDENTIALS_FILE` in `.env`.

6. First run will prompt a browser sign-in to authorize access; token is saved to `token.json`.

## Usage
Create a quiz with a topic and difficulty:
```powershell
python main.py create-quiz "Linear Algebra" medium
```
Outputs:
```
{"formId": "<ID>", "responderUri": "https://docs.google.com/forms/d/e/<ID>/viewform"}
```
Share the `responderUri` link to collect responses.

Grade responses for a form:
```powershell
python main.py grade <formId>
```
Prints a JSON summary with each respondent's score and total points.

## Notes
- The generator uses OpenAI Chat Completions. Provide `OPENAI_API_KEY` in `.env`.
- Questions are validated to exactly 20 items and 4 options each.
- Grading uses the form's stored correct answers and point values; ensure the quiz was created by this tool for best compatibility.

## Troubleshooting
- If the Forms API returns permission errors, ensure the API is enabled and the OAuth client is Desktop type. Try deleting `token.json` and rerunning to reauthorize.
- If JSON parsing fails, rerun; occasionally the LLM may produce malformed JSON. The tool enforces JSON mode to minimize this.
- Use `pip list | Select-String google` to verify google client libraries are installed.
