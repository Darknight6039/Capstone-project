import math
import torch
import nltk
from datasets import Dataset
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
import pandas as pd
from pathlib import Path

nltk.download("punkt")

def load_eval_data(path):
    df = pd.read_csv(path)
    return Dataset.from_pandas(df)

def evaluate_model(model, tokenizer, dataset_path):
    if not Path(dataset_path).exists():
        print("No saved eval set found. You can export it from training and use here.")
        return

    dataset = load_eval_data(dataset_path)
    args = TrainingArguments(output_dir="./eval", per_device_eval_batch_size=1)
    trainer = Trainer(
        model=model,
        args=args,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        eval_dataset=dataset
    )

    print("\n[INFO] Evaluating loss and perplexity...")
    eval_results = trainer.evaluate()
    eval_loss = eval_results.get("eval_loss")
    print(f"Eval loss: {eval_loss:.4f}")
    print(f"Perplexity: {math.exp(eval_loss):.4f}")

    print("\n[INFO] Running ROUGE and BLEU on sample outputs...")
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    rouge1, rougeL, bleu = [], [], []

    for sample in dataset.select(range(10)):
        input_text = sample["text"]
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        output_ids = model.generate(**inputs, max_new_tokens=128)
        pred_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        ref = input_text.split("<|assistant|>")[-1].strip()
        gen = pred_text.split("<|assistant|>")[-1].strip()

        scores = scorer.score(ref, gen)
        rouge1.append(scores["rouge1"].fmeasure)
        rougeL.append(scores["rougeL"].fmeasure)

        ref_tokens = [nltk.word_tokenize(ref)]
        pred_tokens = nltk.word_tokenize(gen)
        bleu.append(sentence_bleu(ref_tokens, pred_tokens))

    print(f"\nROUGE-1: {sum(rouge1)/len(rouge1):.4f}")
    print(f"ROUGE-L: {sum(rougeL)/len(rougeL):.4f}")
    print(f"BLEU:    {sum(bleu)/len(bleu):.4f}")
