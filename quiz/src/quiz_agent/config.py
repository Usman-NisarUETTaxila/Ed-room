import os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cwd_env = Path.cwd() / ".env"
root_env = ROOT / ".env"

# Always attempt to load from project root and CWD, allowing later loads to override earlier ones
if root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)
else:
    load_dotenv(override=True)

if cwd_env.exists():
    load_dotenv(dotenv_path=cwd_env, override=True)

# Last-resort fallback: manual parse if OPENAI_API_KEY still missing (UTF-8 with BOM safe)
def _manual_parse_env(path: Path):
    try:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if "=" in s:
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

if not os.getenv("OPENAI_API_KEY"):
    if root_env.exists():
        _manual_parse_env(root_env)
    if cwd_env.exists():
        _manual_parse_env(cwd_env)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# Default quiz settings
QUIZ_POINTS_PER_QUESTION = 1
QUIZ_SHUFFLE_QUESTIONS = True
QUIZ_TITLE_PREFIX = "Auto Quiz"
