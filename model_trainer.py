"""
Model training module using lightweight transformers for CTF question-answering.
Implements CPU-friendly training with proper validation and checkpointing.
"""

import os
import json
import logging
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForQuestionAnswering,
    TrainingArguments, Trainer, DataCollatorWithPadding
)
from datasets import Dataset as HFDataset
import numpy as np
from typing import List, Dict, Tuple
from sklearn.model_selection import train_test_split

from config import Config

logger = logging.getLogger(__name__)

class CTFDataset(Dataset):
    def __init__(self, examples: List[Dict], tokenizer, max_length: int = 512):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Tokenize question and context
        encoding = self.tokenizer(
            example['question'],
            example['context'],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Find answer positions in context
        answer_start = example['context'].find(example['answer'])
        answer_end = answer_start + len(example['answer'])
        
        # Convert character positions to token positions
        start_positions = encoding.char_to_token(1, answer_start)  # 1 for context sequence
        end_positions = encoding.char_to_token(1, answer_end - 1)
        
        # Handle cases where answer is truncated
        if start_positions is None:
            start_positions = 0
        if end_positions is None:
            end_positions = 0
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'start_positions': torch.tensor(start_positions, dtype=torch.long),
            'end_positions': torch.tensor(end_positions, dtype=torch.long)
        }

class ModelTrainer:
    def __init__(self):
        self.model_name = Config.MODEL_NAME
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
    
    def prepare_training_data(self, processed_data: List[Dict]) -> List[Dict]:
        """Prepare training examples from processed writeups."""
        training_examples = []
        
        for writeup in processed_data:
            examples = writeup.get('training_examples', [])
            for example in examples:
                # Ensure all required fields are present
                if all(key in example for key in ['question', 'context', 'answer']):
                    # Add category information for better learning
                    categories = example.get('categories', [])
                    if categories:
                        category_str = ', '.join(categories)
                        example['question'] = f"[{category_str}] {example['question']}"
                    
                    training_examples.append(example)
        
        logger.info(f"Prepared {len(training_examples)} training examples")
        return training_examples
    
    def split_data(self, examples: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split data into train, validation, and test sets."""
        # First split: 80% train+val, 20% test
        train_val, test = train_test_split(examples, test_size=0.2, random_state=42)
        
        # Second split: 80% train, 20% val (of the remaining 80%)
        train, val = train_test_split(train_val, test_size=0.25, random_state=42)
        
        logger.info(f"Data split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
        return train, val, test
    
    def initialize_model(self):
        """Initialize the model and tokenizer."""
        logger.info(f"Initializing model: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
        
        # Add special tokens for CTF-specific content
        special_tokens = {
            'additional_special_tokens': [
                '[CODE_BLOCK]', '[INLINE_CODE]', '[URL]', '[HASH]', '[HEX]', '[BINARY]'
            ]
        }
        
        self.tokenizer.add_special_tokens(special_tokens)
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        # Move model to device
        self.model.to(self.device)
        
        logger.info(f"Model initialized with {self.model.num_parameters()} parameters")
    
    def create_hf_dataset(self, examples: List[Dict]) -> HFDataset:
        """Create HuggingFace dataset from examples."""
        dataset_dict = {
            'question': [ex['question'] for ex in examples],
            'context': [ex['context'] for ex in examples],
            'answer': [ex['answer'] for ex in examples]
        }
        
        dataset = HFDataset.from_dict(dataset_dict)
        
        def tokenize_function(examples):
            return self.tokenizer(
                examples['question'],
                examples['context'],
                truncation=True,
                padding=True,
                max_length=512
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset
    
    def train(self, processed_data: List[Dict]) -> Dict:
        """Train the model on processed CTF data."""
        logger.info("Starting model training...")
        
        # Initialize model if not already done
        if self.model is None:
            self.initialize_model()
        
        # Prepare training data
        training_examples = self.prepare_training_data(processed_data)
        
        if len(training_examples) < 10:
            raise ValueError("Insufficient training data. Need at least 10 examples.")
        
        # Split data
        train_examples, val_examples, test_examples = self.split_data(training_examples)
        
        # Create datasets
        train_dataset = CTFDataset(train_examples, self.tokenizer)
        val_dataset = CTFDataset(val_examples, self.tokenizer)
        
        # Training arguments optimized for CPU/lightweight training
        training_args = TrainingArguments(
            output_dir=Config.MODEL_SAVE_PATH,
            num_train_epochs=3,
            per_device_train_batch_size=4,  # Small batch size for CPU training
            per_device_eval_batch_size=4,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=os.path.join(Config.MODEL_SAVE_PATH, 'logs'),
            logging_steps=50,
            eval_steps=200,
            save_steps=500,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb logging
            dataloader_num_workers=0,  # Disable multiprocessing for CPU
            fp16=False,  # Disable mixed precision for CPU
        )
        
        # Data collator
        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
        )
        
        # Train the model
        logger.info("Starting training process...")
        trainer.train()
        
        # Save the final model
        trainer.save_model()
        self.tokenizer.save_pretrained(Config.MODEL_SAVE_PATH)
        
        # Get training results
        training_results = {
            'train_examples': len(train_examples),
            'val_examples': len(val_examples),
            'test_examples': len(test_examples),
            'final_eval_loss': trainer.state.log_history[-1].get('eval_loss', 0),
            'total_training_steps': trainer.state.global_step,
            'model_save_path': Config.MODEL_SAVE_PATH
        }
        
        logger.info("Training completed successfully!")
        logger.info(f"Model saved to: {Config.MODEL_SAVE_PATH}")
        
        return training_results
    
    def fine_tune(self, new_data: List[Dict], epochs: int = 1) -> Dict:
        """Fine-tune existing model with new data."""
        if self.model is None:
            logger.info("No existing model found, starting fresh training")
            return self.train(new_data)
        
        logger.info(f"Fine-tuning model with {len(new_data)} new examples")
        
        # Prepare new training data
        training_examples = self.prepare_training_data(new_data)
        train_examples, val_examples, _ = self.split_data(training_examples)
        
        # Create datasets
        train_dataset = CTFDataset(train_examples, self.tokenizer)
        val_dataset = CTFDataset(val_examples, self.tokenizer)
        
        # Fine-tuning arguments (lower learning rate)
        training_args = TrainingArguments(
            output_dir=Config.MODEL_SAVE_PATH,
            num_train_epochs=epochs,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            learning_rate=1e-5,  # Lower learning rate for fine-tuning
            warmup_steps=10,
            weight_decay=0.01,
            logging_steps=25,
            eval_steps=100,
            save_steps=200,
            evaluation_strategy="steps",
            load_best_model_at_end=True,
            report_to=None,
            dataloader_num_workers=0,
            fp16=False,
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
        )
        
        # Fine-tune
        trainer.train()
        trainer.save_model()
        
        return {
            'fine_tune_examples': len(training_examples),
            'epochs': epochs,
            'final_eval_loss': trainer.state.log_history[-1].get('eval_loss', 0)
        }
    
    def save_model(self, path: str = None):
        """Save the trained model."""
        save_path = path or Config.MODEL_SAVE_PATH
        
        if self.model and self.tokenizer:
            self.model.save_pretrained(save_path)
            self.tokenizer.save_pretrained(save_path)
            logger.info(f"Model saved to {save_path}")
        else:
            logger.warning("No model to save")
    
    def load_model(self, path: str = None):
        """Load a saved model."""
        load_path = path or Config.MODEL_SAVE_PATH
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(load_path)
            self.model = AutoModelForQuestionAnswering.from_pretrained(load_path)
            self.model.to(self.device)
            logger.info(f"Model loaded from {load_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        if self.model is None:
            return {'status': 'No model loaded'}
        
        return {
            'model_name': self.model_name,
            'num_parameters': self.model.num_parameters(),
            'device': str(self.device),
            'vocab_size': len(self.tokenizer) if self.tokenizer else 0,
            'max_length': self.tokenizer.model_max_length if self.tokenizer else 0
        }
