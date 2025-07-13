import os
from pathlib import Path

# API Keys
gemini_api_key = os.getenv("GEMINI_API_KEY")
google_api_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# File paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
FAISS_INDEX_PATH.mkdir(exist_ok=True)