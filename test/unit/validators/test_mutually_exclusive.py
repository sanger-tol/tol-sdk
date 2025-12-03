# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import MutuallyExclusiveValidator
from tol.validators.interfaces import Condition


class TestMutuallyExclusiveValidator:
    def test_valid(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'NOT SYMBIONT',
            'RACK_OR_PLATE_ID': 'c',
            'TUBE_OR_WELL_ID': 'd',
        }

        config = MutuallyExclusiveValidator.Config(
            first_field_where=Condition(
                field='SYMBIONT',
                operator='!=',
                value='SYMBIONT',
            ),
            second_field_where=Condition(
                field='SYMBIONT',
                operator='==',
                value='SYMBIONT',
            ),
            target_fields=[
                'RACK_OR_PLATE_ID',
                'TUBE_OR_WELL_ID'
            ],
            error_message='All symbionts must have a TARGET with same rack/plate and tube/well'
        )

        validator = MutuallyExclusiveValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert len(validator.results) == 0
