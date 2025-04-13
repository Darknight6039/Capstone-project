import os
import zipfile
from pathlib import Path
import fitz  # PyMuPDF
import re
import unicodedata
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import get_peft_model, LoraConfig, TaskType
from peft.utils.other import prepare_model_for_kbit_training
import torch

# === Step 1: Unzip the dataset === #
zip_path = Path("/Users/isaiaebongue/Desktop/career_guidance_chatbot_dev/models/training/CV Dataset.zip")
extract_dir = Path("/Users/isaiaebongue/Desktop/career_guidance_chatbot_dev/models/training/datasetunzip")
extract_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print(f"[INFO] Dataset extracted to: {extract_dir.resolve()}")

# === Step 2: Deep text preprocessing === #
def preprocess_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.encode("ascii", errors="ignore").decode("ascii")
    text = re.sub(r"[â€™Ã†ï¼â€œÂ¢¦§©«®°±²³µ·¸¹º»¼½¾¿]", " ", text)
    text = re.sub(r"[•●▪■☆★→⇒➤◆]", " ", text)
    text = re.sub(r"^[0-9\s\-/:.]{5,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[\.\-\*]{3,}", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\b\d{10,}\b", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,;:'\"()\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()

# === Step 3: Extract text from PDFs and apply cleaning === #
cv_data = []
print("\n[INFO] Scanning for PDF CVs and applying preprocessing...\n")

pdf_files = list(extract_dir.rglob("*.pdf"))
print(f"[INFO] Found {len(pdf_files)} PDF files.\n")

for file in pdf_files:
    try:
        doc = fitz.open(file)
        text = "".join(page.get_text() for page in doc)
        doc.close()

        cleaned_text = preprocess_text(text)

        cv_data.append({
            "file_path": str(file),
            "original_length": len(text),
            "cleaned_length": len(cleaned_text),
            "text": cleaned_text
        })

    except Exception as e:
        print(f"[WARNING] Failed to process {file.name}: {e}")

print(f"\n[INFO] Total CVs processed: {len(cv_data)}")

for i, sample in enumerate(cv_data[:2], 1):
    print(f"\n[Sample {i}]")
    print(f"  • Path: {sample['file_path']}")
    print(f"  • Original Length: {sample['original_length']}, Cleaned: {sample['cleaned_length']}")
    print(f"  • Snippet: {sample['text'][:200]}...\n")

# === Step 4: Format prompt-only dataset for instruction tuning === #
def format_cv_entry(entry):
    prompt = f"""<|user|>
Given the following CV, summarize the candidate's qualifications and experience.

CV:
{entry["text"]}

<|assistant|>
"""
    return {"text": prompt}

formatted_data = [format_cv_entry(e) for e in cv_data]
df = pd.DataFrame(formatted_data)
hf_dataset = Dataset.from_pandas(df)

# === Step 5: Load Tokenizer === #
model_id = "microsoft/phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

# === Step 6: Tokenize dataset and add labels === #
def tokenize_for_causal_lm(example):
    tokens = tokenizer(example["text"], truncation=True, padding="max_length", max_length=2048)
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens

tokenized_dataset = hf_dataset.map(tokenize_for_causal_lm, batched=True)

# === Step 7: Quantized loading and LoRA === #
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,
    llm_int8_skip_modules=None,
    llm_int8_enable_fp32_cpu_offload=True
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True,
    quantization_config=bnb_config
)

# ✅ Prepare model for training + apply LoRA
model = prepare_model_for_kbit_training(model)

peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=16,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)

model = get_peft_model(model, peft_config)
model.gradient_checkpointing_enable()
model.config.use_cache = False

model.print_trainable_parameters()

# === Step 8: Training configuration === #
training_args = TrainingArguments(
    output_dir="./phi3-cv-finetuned",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="no",
    learning_rate=2e-5,
    fp16=True,
    bf16=False,
    report_to="none"
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator
)

# === Step 9: Train the model === #
trainer.train()

# === Step 10: Save final model and tokenizer === #
trainer.save_model("./phi3-cv-finetuned")
tokenizer.save_pretrained("./phi3-cv-finetuned")