import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env if present
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5.6-luna"

def get_openai_client():
    """
    Initializes and returns the OpenAI client if key is configured,
    otherwise raises an error.
    """
    if not OPENAI_API_KEY or "your_openai_api_key_here" in OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not configured. Please enter your API key in the local .env file "
            "or set it as an environment variable."
        )
    return OpenAI(api_key=OPENAI_API_KEY)
