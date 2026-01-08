# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import DateCollectionVsPlatingEstimationValidator


class TestDateCollectionVsPlatingEstimationValidator:
    def test_valid_dates_no_error(self) -> None:
        """Test that valid dates with collection before plating produce no errors."""
        # Create a mock object with valid dates
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'valid'
        mock_obj.attributes = {
            'collection_date': '2023-10-15',
            'plating_date': '2023-10-16',
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateCollectionVsPlatingEstimationValidator.Config(
            collection='collection_date',
            plating='plating_date'
        )
        validator = DateCollectionVsPlatingEstimationValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert not validator.results

    def test_collection_after_plating_error(self) -> None:
        """Test that collection date after plating date produces an error."""
        # Create a mock object with collection after plating
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'invalid'
        mock_obj.attributes = {
            'collection_date': '2023-10-17',
            'plating_date': '2023-10-16',
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateCollectionVsPlatingEstimationValidator.Config(
            collection='collection_date',
            plating='plating_date'
        )
        validator = DateCollectionVsPlatingEstimationValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert len(validator.errors) == 1
        assert 'is after plating date' in validator.errors[0].detail

    def test_invalid_collection_format_error(self) -> None:
        """Test that invalid collection date format produces an error."""
        # Create a mock object with invalid collection date
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'invalid_format'
        mock_obj.attributes = {
            'collection_date': 'invalid-date',
            'plating_date': '2023-10-16',
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateCollectionVsPlatingEstimationValidator.Config(
            collection='collection_date',
            plating='plating_date'
        )
        validator = DateCollectionVsPlatingEstimationValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert len(validator.errors) == 1
        assert 'not in the right date format' in validator.errors[0].detail
        assert validator.errors[0].field == 'collection_date'

    def test_invalid_plating_format_error(self) -> None:
        """Test that invalid plating date format produces an error."""
        # Create a mock object with invalid plating date
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'invalid_format'
        mock_obj.attributes = {
            'collection_date': '2023-10-15',
            'plating_date': 'invalid-date',
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateCollectionVsPlatingEstimationValidator.Config(
            collection='collection_date',
            plating='plating_date'
        )
        validator = DateCollectionVsPlatingEstimationValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert len(validator.errors) == 1
        assert 'not in the right date format' in validator.errors[0].detail
        assert validator.errors[0].field == 'plating_date'

    def test_missing_dates_no_error(self) -> None:
        """Test that missing dates do not produce errors."""
        # Create a mock object with missing dates
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'missing'
        mock_obj.attributes = {
            'collection_date': None,
            'plating_date': '2023-10-16',
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateCollectionVsPlatingEstimationValidator.Config(
            collection='collection_date',
            plating='plating_date'
        )
        validator = DateCollectionVsPlatingEstimationValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert not validator.results
