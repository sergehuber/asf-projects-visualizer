import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from openai import OpenAI
from config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, LOCAL_MODEL_NAME

class LLMFactory:
    @staticmethod
    def get_llm():
        if LLM_PROVIDER == 'openai':
            print("Using OpenAI as the LLM provider")
            return OpenAILLM()
        elif LLM_PROVIDER == 'local':
            print("Using local model as the LLM provider")
            return LocalLLM(LOCAL_MODEL_NAME)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

class LocalLLM:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Device selection logic
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        
        print(f"Using device: {self.device}")

        # Load the model with the appropriate dtype
        if self.device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
        self.model = self.model.to(self.device)

    def generate_response(self, prompt, max_length=1024, temperature=0.7, top_p=0.9):
        # Encode the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
        
        # Generate output using the model
        output_ids = self.model.generate(
            input_ids=input_ids,
            max_length=max_length + input_ids.shape[1],
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            no_repeat_ngram_size=2,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Decode the generated tokens to text
        generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Remove the prompt from the generated text to get the response
        response = generated_text[len(prompt):].strip()
        return response
        
class OpenAILLM:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_response(self, prompt, max_tokens=1000):
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert on Apache projects."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

llm = LLMFactory.get_llm()

def query_llm_for_projects(query, project_metadata):
    prompt = f"""
    Your task is to interpret user queries about Apache projects and return 
    a list of relevant Apache project names along with brief explanations for why each project is relevant. Also, 
    describe relationships between the projects and suggest multiple possible stacks of projects.

    Here's a list of Apache projects with short descriptions:
    {project_metadata}

    Given the query: '{query}', what Apache projects would be most relevant, how are they related to each other, and 
    what would be possible stacks of these projects? Please provide the project names, brief explanations for why 
    each project is relevant, its role in the stack, key features, relationships between the projects, and multiple suggested stacks.

    Provide your response in JSON format with the following structure, and never put any text before or after the JSON:
    {{
        "projects": {{
            "project_name": {{
                "explanation": "...",
                "role": "...",
                "features": ["feature1", "feature2", ...]
            }}
        }},
        "relationships": [
            {{
                "source": "project1",
                "target": "project2",
                "description": "relationship_description"
            }}
        ],
        "stacks": [
            {{
                "name": "stack_name",
                "projects": ["project1", "project2", ...],
                "description": "stack_description"
            }}
        ]
    }}
    """
    return query_llm(prompt)

def query_llm(prompt):
    response = llm.generate_response(prompt)
    return response    