from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling

def run_training(model, tokenizer, train_dataset, eval_dataset, output_dir):
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=1,
        logging_dir="./logs",
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        learning_rate=2e-5,
        fp16=True,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    )

    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
