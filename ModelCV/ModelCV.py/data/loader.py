import zipfile
import fitz
import pandas as pd
from datasets import Dataset
from .preprocessing import preprocess_text, format_cv
# import preprocessing
# print(dir(preprocessing))


def extract_texts(zip_path, extract_dir):
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    pdfs = list(extract_dir.rglob("*.pdf"))
    data = []
    for file in pdfs:
        try:
            doc = fitz.open(file)
            text = "".join(p.get_text() for p in doc)
            doc.close()
            data.append({"text": preprocess_text(text)})
        except Exception as e:
            print(f"Skip {file.name}: {e}")
    return data

def prepare_dataset(data, tokenizer):
    formatted = [format_cv(e) for e in data]
    dataset = Dataset.from_pandas(pd.DataFrame(formatted))

    def tokenize(example):
        tokens = tokenizer(example["text"], truncation=True, padding="max_length", max_length=2048)
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    tokenized = dataset.map(tokenize, batched=True)
    return tokenized.train_test_split(test_size=0.2)
