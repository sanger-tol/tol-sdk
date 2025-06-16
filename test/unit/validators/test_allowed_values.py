# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import (
    AllowedValues,
    AllowedValuesValidator,
)


class TestAllowedValuesValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = [
            AllowedValues(
                key='key1',
                values=list('abc')
            ),
            {
                'key': 'key2',
                'values': list('abc')    
            }
        ]

        validator = AllowedValuesValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.results

    def test_warnings(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = [
            AllowedValues(
                key='key1',
                values=list('abc')
            ),
            # adds warnings
            AllowedValues(
                key='key2',
                values=list('xyz'),
                is_error=False,
            ),
        ]

        validator = AllowedValuesValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert validator.has_no_errors
        assert len(validator.results) == 3

    def test_errors(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = [
            AllowedValues(
                key='key1',
                values=list('abc')
            ),
            # adds errors
            AllowedValues(
                key='key2',
                values=list('xyz'),
            ),
        ]

        validator = AllowedValuesValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
