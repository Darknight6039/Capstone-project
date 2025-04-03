import unicodedata
import re

def preprocess_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.encode("ascii", errors="ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\s.,;:'\"()\-]", " ", text)
    return text.lower().strip()

def format_cv(entry):
    return {"text": f"<|user|>\nGiven the following CV, summarize the candidate’s qualifications and experience.\n\nCV:\n{entry['text']}\n\n<|assistant|>\n"}
