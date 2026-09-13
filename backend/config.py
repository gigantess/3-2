import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current dir
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Determine whether to use mock DB (if FIREBASE_SERVICE_ACCOUNT_JSON is not provided)
USE_MOCK_DB_ENV = os.getenv("USE_MOCK_DB", "").lower() in ("true", "1", "yes")
USE_MOCK_DB = USE_MOCK_DB_ENV or (not FIREBASE_SERVICE_ACCOUNT_JSON and not os.path.exists(BASE_DIR / "firebase-credentials.json"))
