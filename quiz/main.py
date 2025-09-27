import argparse
from rich import print
from src.quiz_agent.generator import generate_mcqs, mcqs_to_summary
from src.quiz_agent.forms_api import create_quiz_form, list_responses, _get_service
from src.quiz_agent.config import QUIZ_TITLE_PREFIX
from src.quiz_agent.grader import compute_scores
from pathlib import Path
import json
from datetime import datetime
import time


def _safe_slug(text: str) -> str:
    keep = [c if c.isalnum() or c in ('-', '_') else '-' for c in text.strip()]
    slug = ''.join(keep)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-') or 'quiz'


def cmd_create(topic: str, difficulty: str):
    print(f"[bold green]Generating MCQs[/bold green] for topic='{topic}', difficulty='{difficulty}'...")
    mcqs = generate_mcqs(topic, difficulty)
    title = f"{QUIZ_TITLE_PREFIX}: {topic} ({difficulty})"
    description = f"Auto-generated quiz on {topic} at {difficulty} difficulty."
    form_info = create_quiz_form(title, description, [m.model_dump() for m in mcqs])
    print("[bold blue]Quiz created![/bold blue]")
    print({"formId": form_info["formId"], "responderUri": form_info["responderUri"]})

    # Save outputs to disk
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _safe_slug(topic)

    questions_path = out_dir / f"questions-{slug}-{difficulty}-{ts}.json"
    form_path = out_dir / f"form-{form_info['formId']}-{ts}.json"

    with questions_path.open('w', encoding='utf-8') as f:
        json.dump(mcqs_to_summary(mcqs), f, ensure_ascii=False, indent=2)

    with form_path.open('w', encoding='utf-8') as f:
        json.dump(form_info, f, ensure_ascii=False, indent=2)

    print("[dim]Saved:")
    print(f" - {questions_path}")
    print(f" - {form_path}")


def cmd_grade(form_id: str):
    service = _get_service()
    form = service.forms().get(formId=form_id).execute()
    responses = list_responses(form_id)
    summary = compute_scores(form, responses)
    print(summary)


def main():
    parser = argparse.ArgumentParser(description="AI Quiz Agent for Google Forms")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create-quiz", help="Create a new Google Form quiz")
    p_create.add_argument("topic", type=str, help="Topic name")
    p_create.add_argument("difficulty", type=str, choices=["easy", "medium", "hard"], help="Difficulty level")

    p_grade = sub.add_parser("grade", help="Fetch responses and compute scores")
    p_grade.add_argument("form_id", type=str, help="Google Form ID")

    p_watch = sub.add_parser("watch-grade", help="Continuously watch for new responses and auto-grade")
    p_watch.add_argument("form_id", type=str, help="Google Form ID")
    p_watch.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default 10)")

    args = parser.parse_args()

    if args.command == "create-quiz":
        cmd_create(args.topic, args.difficulty)
    elif args.command == "grade":
        cmd_grade(args.form_id)
    elif args.command == "watch-grade":
        service = _get_service()
        form = service.forms().get(formId=args.form_id).execute()
        seen = set()
        out_dir = Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_scores = out_dir / f"scores-{args.form_id}.jsonl"
        print(f"[bold]Watching for new responses on form {args.form_id}...[/bold]")
        try:
            while True:
                responses = list_responses(args.form_id)
                summary = compute_scores(form, responses)
                for r in summary["results"]:
                    rid = r.get("responseId")
                    if not rid or rid in seen:
                        continue
                    seen.add(rid)
                    # Print a concise result to console
                    print({
                        "responseId": rid,
                        "email": r.get("email"),
                        "score": r.get("score"),
                        "total": r.get("total"),
                    })
                    # Append full details to JSONL
                    with out_scores.open('a', encoding='utf-8') as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped watching.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
