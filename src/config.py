# Copyright 2024 The Apache Software Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_value(key, default=None):
    value = os.environ.get(key, default)
    if value is not None:
        # Remove comments from the value
        value = re.sub(r'#.*$', '', value).strip()
    return value

# LLM Configuration
LLM_PROVIDER = get_env_value('LLM_PROVIDER', 'openai')  # 'openai' or 'local'
print("LLM_PROVIDER: ", LLM_PROVIDER)

# OpenAI Configuration
OPENAI_API_KEY = get_env_value('OPENAI_API_KEY')
OPENAI_MODEL = get_env_value('OPENAI_MODEL', 'gpt-4o')
print("OPENAI_MODEL: ", OPENAI_MODEL)

# Local LLM Configuration
LOCAL_MODEL_NAME = get_env_value('LOCAL_MODEL_NAME', 'model_name')  # Replace with your actual model name
print("LOCAL_MODEL_NAME: ", LOCAL_MODEL_NAME)

# Ensure required environment variables are set
if LLM_PROVIDER == 'openai' and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set when using OpenAI as the LLM provider")
