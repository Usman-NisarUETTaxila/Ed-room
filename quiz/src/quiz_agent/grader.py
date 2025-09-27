from typing import Dict, Any


def compute_scores(form: Dict[str, Any], responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute per-respondent scores using the form's grading and responses.
    Returns summary with each respondent's score and total.
    """
    # Map itemId -> { correctAnswers: [values], pointValue }
    item_map = {}
    for item in form.get("items", []):
        qi = item.get("questionItem")
        if not qi:
            continue
        question = qi.get("question", {})
        grading = question.get("grading", {})
        correct_values = [a.get("value") for a in grading.get("correctAnswers", {}).get("answers", [])]
        item_map[item["itemId"]] = {
            "correct": set(correct_values),
            "points": grading.get("pointValue", 0)
        }

    results = []
    total_points = sum(v["points"] for v in item_map.values())

    for resp in responses.get("responses", []):
        answers = resp.get("answers", {})
        score = 0
        details = []
        for item_id, answer_obj in answers.items():
            choice = None
            if "textAnswers" in answer_obj:
                # Not expected for MCQs; skip
                pass
            elif "choiceAnswers" in answer_obj:
                chosen = answer_obj["choiceAnswers"].get("values", [])
                choice = chosen[0] if chosen else None
            if item_id in item_map and choice is not None:
                is_correct = choice in item_map[item_id]["correct"]
                pts = item_map[item_id]["points"] if is_correct else 0
                score += pts
                details.append({
                    "itemId": item_id,
                    "selected": choice,
                    "correct": list(item_map[item_id]["correct"]),
                    "awarded": pts,
                    "is_correct": is_correct,
                })
        results.append({
            "responseId": resp.get("responseId"),
            "email": resp.get("respondentEmail"),
            "score": score,
            "total": total_points,
            "details": details,
        })

    return {"results": results, "total": total_points}
