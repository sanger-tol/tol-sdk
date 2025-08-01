# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments
from datasets import load_dataset
from .dataset_processor import DatasetProcessor

class ModelTraining:
    """
    
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

        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        model = T5ForConditionalGeneration.from_pretrained("t5-small")

        # Convert to proper format
        train_list = self.prepare_data(train_data['train'])
        val_list = self.prepare_data(train_data['test'])

        train_dataset = DatasetProcessor(train_list, tokenizer)
        val_dataset = DatasetProcessor(val_list, tokenizer)

        training_args = TrainingArguments(
            output_dir="src/tol/ai/t5-jsongen-finetuned",
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            num_train_epochs=5,  # Increased epochs
            learning_rate=5e-5,  # Explicit learning rate
            warmup_steps=100,
            logging_steps=10,
            eval_steps=50,
            save_steps=50,
            save_total_limit=2,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            gradient_checkpointing=True,  # Save memory
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer
        )

        trainer.train()
        
        trainer.save_model("src/tol/ai/t5-jsongen-finetuned")
        tokenizer.save_pretrained("src/tol/ai/t5-jsongen-finetuned")
    