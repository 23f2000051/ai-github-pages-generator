# app/config.py (simple)
from pathlib import Path
from dotenv import load_dotenv
import os

# 1) Load .env from project root (two levels up from this file)
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    load_dotenv(env_path)   # loads into environment; does not override actual env vars

# 2) Read configuration into module-level values
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER", "your-github-username")
API_SECRET = os.getenv("API_SECRET")   # optional: verify requests only if set
SKIP_GITHUB = os.getenv("SKIP_GITHUB", "0") == "1"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
# Optional: model name to use for Gemini
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Default repo privacy setting (treat '1' as true)
DEFAULT_REPO_PRIVATE = os.getenv("DEFAULT_REPO_PRIVATE", "0") == "1"