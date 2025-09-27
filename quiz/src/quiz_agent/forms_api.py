from __future__ import annotations
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json

from .config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_TOKEN_FILE,
    QUIZ_POINTS_PER_QUESTION,
    QUIZ_SHUFFLE_QUESTIONS,
    QUIZ_TITLE_PREFIX,
)

# OAuth scopes required
# forms.body -> create and modify form content
# forms.body.readonly -> read form content
# forms.responses.readonly -> read responses for grading
# drive.file -> allow the app to create and manage files it creates in the user's Drive (needed when creating new Forms)
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def _get_service():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    service = build("forms", "v1", credentials=creds)
    return service


def create_quiz_form(title: str, description: str, mcqs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates a Google Form with quiz settings and 20 multiple choice questions.
    mcqs: list of dicts: {question, options[4], answer_index, explanation?}
    Returns: dict with formId, responderUri, and created items structure mapping.
    """
    service = _get_service()

    # 1) Create empty form (only title allowed at create time)
    form = {"info": {"title": title}}
    created = service.forms().create(body=form).execute()
    form_id = created["formId"]

    # 2) Build batchUpdate requests to add questions
    requests: List[Dict[str, Any]] = []

    # First update: set description via updateFormInfo
    requests.append(
        {
            "updateFormInfo": {
                "info": {
                    "title": title,
                    "description": description,
                },
                "updateMask": "title,description"
            }
        }
    )

    for idx, q in enumerate(mcqs):
        requests.append(
            {
                "createItem": {
                    "item": {
                        "title": q["question"],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": opt} for opt in q["options"]],
                                    "shuffle": False,
                                }
                            }
                        },
                        "description": q.get("explanation", "")
                    },
                    "location": {"index": idx}
                }
            }
        )

    # 3) Execute batchUpdate to add items
    batch = service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

    # 4) Fetch the form to get item IDs
    full_form = service.forms().get(formId=form_id).execute()

    # 5) Mark as quiz and set correct answers/points
    # Note: As of Forms API v1, grading is set via update requests on question.grading
    # We'll construct update requests to set correct answers and point values.
    grading_requests: List[Dict[str, Any]] = [
        {
            "updateSettings": {
                "settings": {
                    "quizSettings": {
                        "isQuiz": True
                    }
                },
                "updateMask": "quizSettings.isQuiz"
            }
        }
    ]

    # Map each created question to its itemId and set grading
    q_items = [it for it in full_form.get("items", []) if "questionItem" in it]

    for idx, item in enumerate(q_items):
        item_id = item["itemId"]
        correct_index = mcqs[idx]["answer_index"]
        correct_option_value = mcqs[idx]["options"][correct_index]

        grading_requests.append(
            {
                "updateItem": {
                    "item": {
                        "itemId": item_id,
                        "questionItem": {
                            "question": {
                                "grading": {
                                    "pointValue": QUIZ_POINTS_PER_QUESTION,
                                    "correctAnswers": {
                                        "answers": [
                                            {"value": correct_option_value}
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    "location": {"index": idx},
                    "updateMask": "questionItem.question.grading"
                }
            }
        )

    service.forms().batchUpdate(formId=form_id, body={"requests": grading_requests}).execute()

    # Get responder URL
    form_after = service.forms().get(formId=form_id).execute()
    responder_uri = form_after.get("responderUri")

    return {
        "formId": form_id,
        "responderUri": responder_uri,
        "created": form_after,
    }


def list_responses(form_id: str) -> Dict[str, Any]:
    service = _get_service()
    try:
        return service.forms().responses().list(formId=form_id).execute()
    except HttpError as e:
        raise RuntimeError(f"Failed to list responses: {e}")
