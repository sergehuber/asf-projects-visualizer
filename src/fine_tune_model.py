import json
from transformers import TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from huggingface_hub import login
import os

# Add these lines before loading the tokenizer
login(token=os.environ.get("HUGGINGFACE_TOKEN"))

# Load Apache project data
with open('apache_projects_raw.json', 'r') as f:
    apache_projects = json.load(f)

# Prepare training data
def prepare_training_data():
    data = []
    for project in apache_projects:
        text = f"Project: {project['name']}\n"
        text += f"Description: {project['shortdesc']}\n"
        text += f"Category: {project['category']}\n"
        text += f"Features: {', '.join(project.get('features', []))}\n\n"
        data.append(text)
    
    with open('apache_projects_data.txt', 'w') as f:
        f.write('\n'.join(data))

# Determine the device
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print(f"Using device: {device}")

# Download and prepare the model
model_name = "meta-llama/Llama-3.2-1B"  # You can change this to other Llama variants

# Load model directly

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Move model to the appropriate device
model = model.to(device)

# Prepare the dataset
def load_dataset(file_path, tokenizer):
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=file_path,
        block_size=128)
    return dataset

# Fine-tune the model
def fine_tune_model():
    prepare_training_data()
    
    train_dataset = load_dataset('apache_projects_data.txt', tokenizer)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    output_dir = "./llama-apache-projects"

    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=10_000,
        save_total_limit=2,
        fp16=(device.type == "cuda"),  # Enable mixed precision only for CUDA
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    trainer.train()
    trainer.save_model()
    # Explicitly save the tokenizer
    tokenizer.save_pretrained(output_dir)
    print(f"Model and tokenizer saved to {output_dir}")

if __name__ == "__main__":
    fine_tune_model()
