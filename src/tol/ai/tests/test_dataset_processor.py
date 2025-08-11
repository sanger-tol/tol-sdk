# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import unittest
import torch
from types import SimpleNamespace
from ..dataset_processor import DatasetProcessor


class MockTokenizer:
    def __init__(self, pad_token_id=0):
        self.pad_token_id = pad_token_id

    def __call__(self, text, max_length, padding, truncation, return_tensors):
        # Simulate tokenization by returning a fixed-size tensor filled with dummy token ids
        input_ids = torch.zeros((1, max_length), dtype=torch.long)
        input_ids[0, :2] = 1  # Set first 2 tokens to 1, rest remain 0 (pad tokens)
        
        attention_mask = torch.zeros((1, max_length), dtype=torch.long)
        attention_mask[0, :2] = 1  # Only attend to first 2 tokens, ignore padding
        return {"input_ids": input_ids, "attention_mask": attention_mask}


class TestDatasetProcessor(unittest.TestCase):
    def setUp(self):
        self.data = [
            {
                "input_text": "make a board with a tissue_prep zone that has a table showing Downstream Protocol",
                "target_text": "{""zone"": {""object_type"": ""tissue_prep"", ""components"": [{""table"": {""title"": ""random"", ""attributes"": [""benchling_downstream_protocol""]}}]}}"
            },
            {
                "input_text": "generate a assembly_analysis zone that has a table showing Analysis ID",
                "target_text": "{""zone"": {""object_type"": ""assembly_analysis"", ""components"": [{""table"": {""title"": ""random"", ""attributes"": [""id""]}}]}}"
            }
        ]
        self.tokenizer = MockTokenizer(pad_token_id=0)
        self.dataset = DatasetProcessor(self.data, self.tokenizer, max_input_len=30, max_output_len=50)

    def test_len(self):
        self.assertEqual(len(self.dataset), 2)

    def test_getitem_structure(self):
        item = self.dataset[0]
        self.assertIn("input_ids", item)
        self.assertIn("attention_mask", item)
        self.assertIn("labels", item)

    def test_tensor_shapes(self):
        item = self.dataset[0]
        self.assertEqual(item["input_ids"].shape, torch.Size([30]))
        self.assertEqual(item["attention_mask"].shape, torch.Size([30]))
        self.assertEqual(item["labels"].shape, torch.Size([50]))

    def test_labels_padding_replaced_with_minus_100(self):
        # Create a new mock tokenizer with pad_token_id=0
        mock_tokenizer = MockTokenizer(pad_token_id=0)
        
        # Track calls to differentiate between input and target tokenization
        call_count = 0
        
        def mock_tokenizer_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:  # First call is for input text
                return {
                    "input_ids": torch.tensor([[1, 2, 3, 4, 5, 0, 0, 0, 0, 0]]),
                    "attention_mask": torch.ones((1, 10), dtype=torch.long)
                }
            else:  # Second call is for target text - this becomes labels
                return {
                    "input_ids": torch.tensor([[1, 2, 0, 0, 0, 0, 0, 0, 0, 0]]),
                    "attention_mask": torch.ones((1, 10), dtype=torch.long)
                }
        
        mock_tokenizer.__call__ = mock_tokenizer_call
        
        # Create dataset with the properly configured mock tokenizer
        new_dataset = DatasetProcessor(self.data, mock_tokenizer, max_input_len=10, max_output_len=10)
        item = new_dataset[0]
        print("Labels:", item["labels"])
        print("Tokenizer pad_token_id:", mock_tokenizer.pad_token_id)
        # Check that positions 2 and beyond (which were pad tokens with id=0) are now -100
        self.assertTrue(torch.all(item["labels"][2:] == -100))
        # Check that the first two positions are not -100 (they were actual tokens)
        self.assertTrue(torch.all(item["labels"][:2] != -100))


if __name__ == "__main__":
    unittest.main()