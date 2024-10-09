import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from openai import OpenAI
from config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, LOCAL_MODEL_NAME, LOCAL_MODEL_PATH

class LLMFactory:
    @staticmethod
    def get_llm():
        if LLM_PROVIDER == 'openai':
            return OpenAILLM()
        elif LLM_PROVIDER == 'local':
            return LocalLLM(LOCAL_MODEL_NAME, LOCAL_MODEL_PATH)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

class LocalLLM:
    def __init__(self):
        self.model_name = "gpt2-xl"
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
        
        # Set pad token to eos token
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.config.pad_token_id = self.model.config.eos_token_id

        # Move model to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def generate_response(self, prompt):
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", truncation=True, max_length=1600)
        inputs = inputs.to(self.device)
        
        attention_mask = torch.ones(inputs.shape, dtype=torch.long, device=self.device)
        
        outputs = self.model.generate(
            inputs,
            attention_mask=attention_mask,
            max_length=1600,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
class OpenAILLM:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_response(self, prompt, max_tokens=500):
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

def query_llm(query, project_metadata):
    prompt = f"""
    Your task is to interpret user queries about Apache projects and return 
    a list of relevant Apache project names along with brief explanations for why each project is relevant. Also, 
    describe relationships between the projects and suggest multiple possible stacks of projects.

    Here's a list of Apache projects with short descriptions:
    {project_metadata}

    Given the query: '{query}', what Apache projects would be most relevant, how are they related to each other, and 
    what would be possible stacks of these projects? Please provide the project names, brief explanations for why 
    each project is relevant, its role in the stack, key features, relationships between the projects, and multiple suggested stacks.

    Provide your response in JSON format with the following structure:
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
    print("Querying LLM with prompt:")
    print(prompt)
    response = llm.generate_response(prompt)
    print("LLM response:")
    print(response)
    return response