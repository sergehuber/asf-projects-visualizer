import os

# LLM Configuration
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')  # 'openai' or 'local'

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')

# Local LLM Configuration
LOCAL_MODEL_NAME = os.environ.get('LOCAL_MODEL_NAME', 'model_name')  # Replace with your actual model name

# Ensure required environment variables are set
if LLM_PROVIDER == 'openai' and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set when using OpenAI as the LLM provider")
