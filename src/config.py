import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')  # 'openai' or 'local'
print("LLM_PROVIDER: ", LLM_PROVIDER)

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
print("OPENAI_MODEL: ", OPENAI_MODEL)
# Local LLM Configuration
LOCAL_MODEL_NAME = os.environ.get('LOCAL_MODEL_NAME', 'model_name')  # Replace with your actual model name
print("LOCAL_MODEL_NAME: ", LOCAL_MODEL_NAME)

# Ensure required environment variables are set
if LLM_PROVIDER == 'openai' and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set when using OpenAI as the LLM provider")
