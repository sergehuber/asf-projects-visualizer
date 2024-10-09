import json
from transformers import GPT2Tokenizer, GPT2LMHeadModel, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments

# Load Apache project data
with open('apache_projects.json', 'r') as f:
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

# Download and prepare the model
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

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

    training_args = TrainingArguments(
        output_dir="./models/gpt2-apache-projects",
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=10_000,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    trainer.train()
    trainer.save_model()

if __name__ == "__main__":
    fine_tune_model()
