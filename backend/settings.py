"""Local configuration for the standard-library server."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

HOST = "127.0.0.1"
PORT = 8000
DATABASE_PATH = BASE_DIR / "data.sqlite3"
CORS_ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}

# Paste the Gemini key here before starting the server.
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-3.7-flash"
GEMINI_BATCH_SIZE = 25
DEMO_MODE = False
NEGATIVE_SPIKE_MIN_MESSAGES = 3
NEGATIVE_SPIKE_MULTIPLIER = 1.5
NEGATIVE_SPIKE_RATE = 0.35
