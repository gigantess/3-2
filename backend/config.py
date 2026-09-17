import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current dir
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Candidate credentials file paths
CRED_PATHS = [
    BASE_DIR / ".security" / "firebase-credentials.json",
    BASE_DIR / "firebase-credentials.json"
]
HAS_LOCAL_CREDS = any(p.exists() for p in CRED_PATHS)

# Determine whether to use mock DB (if neither env json nor credentials files are found)
USE_MOCK_DB_ENV = os.getenv("USE_MOCK_DB", "").lower() in ("true", "1", "yes")
USE_MOCK_DB = USE_MOCK_DB_ENV or (not FIREBASE_SERVICE_ACCOUNT_JSON and not HAS_LOCAL_CREDS)

