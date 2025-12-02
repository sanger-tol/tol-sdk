# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import MutuallyExclusiveValidator
from tol.validators.interfaces import Condition


class TestMutuallyExcludiveValidator:
    def test_valid(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
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
