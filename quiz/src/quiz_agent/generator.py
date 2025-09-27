from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class MCQ(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: str | None = None
    difficulty: str | None = None


def _build_prompt(topic: str, difficulty: str) -> str:
    template = (
        "You are an expert assessment designer. Create EXACTLY 20 high-quality multiple-choice questions "
        "for the topic \"{topic}\" at \"{difficulty}\" difficulty.\n\n"
        "CRITICAL: You must generate exactly 20 questions, no more, no less.\n\n"
        "Output JSON only with this exact structure (no markdown):\n"
        "{{\n"
        "  \"questions\": [\n"
        "    {{\n"
        "      \"question\": \"...\",\n"
        "      \"options\": [\"A\", \"B\", \"C\", \"D\"],\n"
        "      \"answer_index\": 0,\n"
        "      \"explanation\": \"...\",\n"
        "      \"difficulty\": \"{difficulty}\"\n"
        "    }}\n"
        "  ]\n"
        "}}\n\n"
        "STRICT Constraints:\n"
        "- EXACTLY 20 questions (count them carefully)\n"
        "- EXACTLY 4 options per question\n"
        "- The correct option index is 0-3 in \"answer_index\"\n"
        "- Keep questions unambiguous and not opinion-based\n"
        "- Prefer varied cognitive levels (recall, apply, analyze) within the given difficulty\n"
        "- Double-check that you have exactly 20 questions before responding\n"
    )
    return template.format(topic=topic, difficulty=difficulty).strip()


def filter_to_20_questions(mcqs: List[MCQ]) -> List[MCQ]:
    """
    Manually filter questions to ensure exactly 20 valid questions
    
    Args:
        mcqs: List of MCQ objects to filter
        
    Returns:
        List of exactly 20 valid MCQ objects (or as many as possible if less than 20)
    """
    if not mcqs:
        return []
    
    # Filter for valid questions
    valid_mcqs = []
    for mcq in mcqs:
        # Check if question is valid
        if (mcq.question and 
            mcq.options and 
            len(mcq.options) == 4 and 
            0 <= mcq.answer_index < 4 and
            all(option.strip() for option in mcq.options)):  # All options have content
            valid_mcqs.append(mcq)
    
    # If we have exactly 20 or more, take the first 20
    if len(valid_mcqs) >= 20:
        return valid_mcqs[:20]
    
    # If we have fewer than 20 but more than 0, return what we have
    if valid_mcqs:
        return valid_mcqs
    
    # If no valid questions, return empty list
    return []


def generate_mcqs(topic: str, difficulty: str) -> List[MCQ]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = _build_prompt(topic, difficulty) + "\n\nREMINDER: Generate EXACTLY 20 questions. Count them before responding. No more, no less than 20."

    import json, re

    def try_load(content: str) -> List[MCQ]:
        # Attempt direct parse
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract outermost JSON object
            m = re.search(r"\{[\s\S]*\}", content)
            if not m:
                return []
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                return []
        items = data.get("questions", []) if isinstance(data, dict) else []
        out: List[MCQ] = []
        for q in items:
            try:
                out.append(MCQ(**q))
            except Exception:
                return []
        return out

    last_content = ""
    for attempt in range(3):
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            messages=[
                {"role": "system", "content": "You output strict JSON, no markdown or commentary."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
        )

        content = completion.choices[0].message.content or ""
        last_content = content
        mcqs = try_load(content)

        # Manual filtering to ensure exactly 20 valid questions
        filtered_mcqs = filter_to_20_questions(mcqs)
        if len(filtered_mcqs) == 20:
            return filtered_mcqs

        # Attempt a repair pass asking the model to correct to exactly 20 items
        repair_messages = [
            {"role": "system", "content": "You output strict JSON, no markdown or commentary."},
            {"role": "user", "content": (
                "Fix the following JSON so it strictly matches the schema and contains exactly 20 questions with 4 options each. "
                "Use indices 0-3 for answer_index. Output JSON only.\n\n" + (last_content[:6000])
            )},
        ]
        repair = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=repair_messages,
            response_format={"type": "json_object"},
            max_tokens=4000,
        )
        repaired = repair.choices[0].message.content or ""
        mcqs = try_load(repaired)
        
        # Apply manual filtering again after repair
        filtered_mcqs = filter_to_20_questions(mcqs)
        if len(filtered_mcqs) == 20:
            return filtered_mcqs

    # If we still don't have exactly 20 questions after all attempts, apply final filtering
    if mcqs:
        final_filtered = filter_to_20_questions(mcqs)
        if len(final_filtered) >= 10:  # Accept if we have at least 10 valid questions
            return final_filtered[:20] if len(final_filtered) > 20 else final_filtered
    
    # If still not valid after retries, raise an informative error
    raise RuntimeError(
        f"Could not generate 20 valid questions after retries. Got {len(mcqs)} questions. "
        f"Last partial content starts with: {last_content[:200]}"
    )


def mcqs_to_summary(mcqs: List[MCQ]) -> List[Dict[str, Any]]:
    return [q.model_dump() for q in mcqs]
