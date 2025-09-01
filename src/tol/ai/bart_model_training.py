# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments
from datasets import load_dataset
from .dataset_processor import DatasetProcessor

class BartModelTraining:
    """
    Fine-tune BART model for conditional generation using CSV dataset.
    """

    def __init__(self) -> None:
        pass
    
    def prepare_data(self, dataset):
        """Convert dataset to list format with proper structure"""
        prepared_data = []
        for item in dataset:
            prepared_data.append({
                "input_text": item["input_text"],
                "target_text": item["target_text"]
            })
        return prepared_data

    def train_model(self) -> None:
        # Load your dataset
        dataset = load_dataset('csv', data_files={'train': 'src/tol/ai/expanded_training_data.csv'})
        train_data = dataset['train'].train_test_split(test_size=0.2)

        tokenizer = BartTokenizer.from_pretrained("facebook/bart-base")
        model = BartForConditionalGeneration.from_pretrained("facebook/bart-base")

        # Convert to proper format
        train_list = self.prepare_data(train_data['train'])
        val_list = self.prepare_data(train_data['test'])

        train_dataset = DatasetProcessor(train_list, tokenizer)
        val_dataset = DatasetProcessor(val_list, tokenizer)

        training_args = TrainingArguments(
            output_dir="src/tol/ai/bart-jsongen-finetuned",
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            num_train_epochs=5,
            learning_rate=5e-5,
            warmup_steps=100,
            logging_steps=10,
            eval_steps=50,
            save_steps=50,
            save_total_limit=2,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            gradient_checkpointing=True,
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer
        )

        trainer.train()
        
        trainer.save_model("src/tol/ai/bart-jsongen-finetuned")
        tokenizer.save_pretrained("src/tol/ai/bart-jsongen-finetuned")
