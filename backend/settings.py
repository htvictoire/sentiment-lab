"""Configuration locale du serveur de sentiment."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

HOST = "127.0.0.1"
PORT = 8000
DATABASE_PATH = BASE_DIR / "data.sqlite3"
CORS_ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}

# Le script d'entraînement télécharge ce modèle de base une seule fois, puis
# enregistre le classifieur entraîné sous LOCAL_MODEL_PATH.
LOCAL_MODEL_NAME = "Davlan/afro-xlmr-small"
TRAINING_DATA_PATH = BASE_DIR / "training_data.jsonl"
LOCAL_MODEL_PATH = BASE_DIR / "model_artifacts" / "afroxlmr_sentiment"
LOCAL_INFERENCE_BATCH_SIZE = 4
NEGATIVE_SPIKE_MIN_MESSAGES = 3
NEGATIVE_SPIKE_MULTIPLIER = 1.5
NEGATIVE_SPIKE_RATE = 0.35
