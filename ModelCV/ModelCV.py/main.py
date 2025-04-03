from transformers import AutoTokenizer
from config import ZIP_PATH, EXTRACT_DIR, MODEL_ID, OUTPUT_DIR
from data.loader import extract_texts, prepare_dataset
from modeling.model_setup import load_model
from training.train import run_training

# === Load Data === #
data = extract_texts(ZIP_PATH, EXTRACT_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
dataset_split = prepare_dataset(data, tokenizer)

# === Load Model === #
model = load_model(MODEL_ID)

# === Train === #
run_training(model, tokenizer, dataset_split["train"], dataset_split["test"], OUTPUT_DIR)
