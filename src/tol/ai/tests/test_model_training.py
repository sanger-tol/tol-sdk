# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import Mock, patch
from ..T5_model_training import T5ModelTraining  # Adjust import path


class TestModelTraining:
    """Test suite for ModelTraining class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.model_training = T5ModelTraining()
        
        # Sample training data that matches your use case
        self.sample_data = [
            {
                "input_text": "show me a board with a run_data zone that has a table showing ID",
                "target_text": '{"zone": {"object_type": "run_data", "components": [{"table": {"title": "random", "attributes": ["id"]}}]}}'
            },
            {
                "input_text": "create a sample_data zone with a chart displaying name and value",
                "target_text": '{"zone": {"object_type": "sample_data", "components": [{"chart": {"title": "chart", "attributes": ["name", "value"]}}]}}'
            }
        ]

    def test_init(self):
        """Test ModelTraining initialization"""
        mt = T5ModelTraining()
        assert isinstance(mt, T5ModelTraining)

    def test_prepare_data_with_json_output(self):
        """Test prepare_data with realistic text-to-JSON data"""
        result = self.model_training.prepare_data(self.sample_data)
        
        assert len(result) == 2
        assert result[0]["input_text"] == "show me a board with a run_data zone that has a table showing ID"
        assert '"zone"' in result[0]["target_text"]
        assert '"object_type": "run_data"' in result[0]["target_text"]

    def test_prepare_data_empty_dataset(self):
        """Test prepare_data with empty dataset"""
        result = self.model_training.prepare_data([])
        assert result == []

    def test_prepare_data_missing_keys(self):
        """Test prepare_data with missing required keys"""
        invalid_data = [{"input_text": "some input"}]  # Missing target_text
        
        with pytest.raises(KeyError):
            self.model_training.prepare_data(invalid_data)

    @patch('tol.ai.model_training.load_dataset')
    @patch('tol.ai.model_training.T5Tokenizer')
    @patch('tol.ai.model_training.T5ForConditionalGeneration')
    @patch('tol.ai.model_training.DatasetProcessor')
    @patch('tol.ai.model_training.Trainer')
    def test_train_model_success(
        self, mock_trainer_class, mock_dataset_processor, 
        mock_model_class, mock_tokenizer_class, mock_load_dataset
    ):
        """Test successful model training"""
        # Mock dataset
        mock_dataset_data = Mock()
        mock_dataset_data.train_test_split.return_value = {
            'train': self.sample_data,
            'test': self.sample_data[:1]
        }
        mock_load_dataset.return_value = {'train': mock_dataset_data}
        
        # Mock components
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()
        mock_dataset_processor.return_value = Mock()
        mock_trainer = Mock()
        mock_trainer_class.return_value = mock_trainer
        
        # Run training
        self.model_training.train_model()
        
        # Verify key calls
        mock_load_dataset.assert_called_once()
        mock_trainer.train.assert_called_once()
        mock_trainer.save_model.assert_called_once_with("src/tol/ai/t5-jsongen-finetuned")

    @patch('tol.ai.model_training.load_dataset')
    def test_train_model_dataset_not_found(self, mock_load_dataset):
        """Test train_model when dataset file doesn't exist"""
        mock_load_dataset.side_effect = FileNotFoundError("CSV file not found")
        
        with pytest.raises(FileNotFoundError):
            self.model_training.train_model()

    @patch('tol.ai.model_training.load_dataset')
    @patch('tol.ai.model_training.T5Tokenizer')
    @patch('tol.ai.model_training.T5ForConditionalGeneration')
    @patch('tol.ai.model_training.DatasetProcessor')
    @patch('tol.ai.model_training.Trainer')
    def test_train_model_uses_correct_parameters(
        self, mock_trainer_class, mock_dataset_processor,
        mock_model_class, mock_tokenizer_class, mock_load_dataset
    ):
        """Test that training uses correct parameters"""
        # Setup mocks
        mock_dataset_data = Mock()
        mock_dataset_data.train_test_split.return_value = {'train': self.sample_data, 'test': []}
        mock_load_dataset.return_value = {'train': mock_dataset_data}
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()
        mock_dataset_processor.return_value = Mock()
        mock_trainer_class.return_value = Mock()
        
        # Run training
        self.model_training.train_model()
        
        # Check training arguments
        call_args = mock_trainer_class.call_args[1]['args']
        assert call_args.output_dir == "src/tol/ai/t5-jsongen-finetuned"
        assert call_args.per_device_train_batch_size == 2
        assert call_args.num_train_epochs == 5
        assert call_args.learning_rate == 5e-5


# Test with realistic data patterns
@pytest.mark.parametrize("input_text,expected_object_type", [
    ("show me a board with a run_data zone that has a table showing scientific name", "run_data"),
    ("create a sample zone with a table showing id", "sample"),
    ("create a board that has a table with species name and taxon group", "species"),
])
def test_prepare_data_patterns(input_text, expected_object_type):
    """Test prepare_data maintains data patterns correctly"""
    mt = T5ModelTraining()
    test_data = [{
        "input_text": input_text,
        "target_text": f'{{"zone": {{"object_type": "{expected_object_type}"}}}}'
    }]
    
    result = mt.prepare_data(test_data)
    
    assert len(result) == 1
    assert result[0]["input_text"] == input_text
    assert expected_object_type in result[0]["target_text"]


@pytest.fixture
def json_training_data():
    """Fixture with realistic JSON training data"""
    return [
        {
            "input_text": "generate a board with a family zone that has a table showing Family",
            "target_text": '{""zone"": {""object_type"": ""family"", ""components"": [{""table"": {""title"": ""random"", ""attributes"": [""id""]}}]}}'
        },
        {
            "input_text": "generate a assembly_analysis zone that has a table showing Analysis ID",
            "target_text": '{""zone"": {""object_type"": ""assembly_analysis"", ""components"": [{""table"": {""title"": ""random"", ""attributes"": [""id""]}}]}}'
        }
    ]


def test_prepare_data_with_fixture(json_training_data):
    """Test prepare_data using fixture data"""
    mt = T5ModelTraining()
    result = mt.prepare_data(json_training_data)
    
    assert len(result) == 2
    assert all("input_text" in item and "target_text" in item for item in result)
    assert '"table"' in result[0]["target_text"]
    assert '"assembly_analysis"' in result[1]["target_text"]
