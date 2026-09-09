import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Gemini Config (Checks GEMINI_API_KEY or GOOGLE_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

# Parallel Search API Config
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY", "")

# Google Cloud & Vertex AI Agent Builder Config
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_BUILDER_DATASTORE_ID = os.getenv("AGENT_BUILDER_DATASTORE_ID", "")

def is_gemini_connected() -> bool:
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 5)

def is_agent_builder_connected() -> bool:
    return bool(GOOGLE_CLOUD_PROJECT and AGENT_BUILDER_DATASTORE_ID)

