import os
import json
import tempfile
from pathlib import Path

# API Keys
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Handle Google credentials
google_credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
google_api_key = None

if google_credentials_json:
    try:
        # Parse the JSON credentials
        credentials_data = json.loads(google_credentials_json)
        
        # Create a temporary file with the credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(credentials_data, temp_file)
            google_api_key = temp_file.name
            
        # Set the environment variable for Google libraries to use
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_api_key
    except json.JSONDecodeError as e:
        print(f"Error parsing Google credentials JSON: {e}")
        google_api_key = None
else:
    # Fallback to local file path for development
    local_credentials_path = "/Users/ashaypatel/Documents/UI_RAG_25/keys/rag-25-1d93449ac55d.json"
    if os.path.exists(local_credentials_path):
        google_api_key = local_credentials_path
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_api_key

# File paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
FAISS_INDEX_PATH.mkdir(exist_ok=True)