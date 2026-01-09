# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import DateSortingValidator


class TestDateSortingValidator:
    def test_valid(self) -> None:
        """Test the dates are valid"""
        # Create a mock object with valid dates
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'a'
        mock_obj.attributes = {
            'collection_date': datetime(2023, 10, 15, tzinfo=timezone.utc),  # '2023-10-15'
            'plating_date': datetime(2023, 10, 16, tzinfo=timezone.utc)  # '2023-10-16'
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateSortingValidator.Config(
            dates=['collection_date', 'plating_date']
        )
        validator = DateSortingValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert not validator.results

    def test_invalid(self) -> None:
        """Test that collection date after plating date produces an error."""
        # Create a mock object with collection after plating
        mock_obj: DataObject = create_autospec(DataObject)
        mock_obj.id = 'b'
        mock_obj.attributes = {
            'collection_date': '2023-10-17',
            'plating_date': '2023-10-16'
        }
        mock_obj.get_field_by_name.side_effect = lambda field: mock_obj.attributes.get(field)

        config = DateSortingValidator.Config(
            dates=['collection_date', 'plating_date']
        )
        validator = DateSortingValidator(config)

        # Consume the Iterable
        list(validator.validate(iter([mock_obj])))

        assert len(validator.errors) == 1
        assert 'is before previous date' in validator.errors[0].detail
