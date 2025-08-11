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
        input_ids = torch.ones((1, max_length), dtype=torch.long)
        attention_mask = torch.ones((1, max_length), dtype=torch.long)
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
        self.dataset = DatasetProcessor(self.data, self.tokenizer, max_input_len=10, max_output_len=10)

    def test_len(self):
        self.assertEqual(len(self.dataset), 2)

    def test_getitem_structure(self):
        item = self.dataset[0]
        self.assertIn("input_ids", item)
        self.assertIn("attention_mask", item)
        self.assertIn("labels", item)

    def test_tensor_shapes(self):
        item = self.dataset[0]
        self.assertEqual(item["input_ids"].shape, torch.Size([10]))
        self.assertEqual(item["attention_mask"].shape, torch.Size([10]))
        self.assertEqual(item["labels"].shape, torch.Size([10]))

    def test_labels_padding_replaced_with_minus_100(self):
        # Simulate pad_token_id in target input_ids to test label masking
        self.tokenizer.__call__ = lambda *args, **kwargs: {
            "input_ids": torch.tensor([[1, 2, 0, 0, 0, 0, 0, 0, 0, 0]]),
            "attention_mask": torch.ones((1, 10), dtype=torch.long)
        }
        item = self.dataset[0]
        self.assertTrue(torch.all((item["labels"][2:] == -100)))


if __name__ == "__main__":
    unittest.main()