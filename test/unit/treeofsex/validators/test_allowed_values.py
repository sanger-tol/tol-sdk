# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject
from tol.treeofsex.validators import (
    AllowedValues,
    AllowedValuesValidator,
)


@pytest.fixture
def mock_objs() -> Iterable[DataObject]:

    def __mock_obj(c: str) -> DataObject:
        __o: DataObject = create_autospec(
            DataObject,
        )

        __o.id = c
        __o.attributes = {
            'key1': c,
            'key2': c,
        }
        __o.key1 = c
        __o.key2 = c

        return __o

    return [
        __mock_obj(c) for c in 'abc'
    ]


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
            AllowedValues(
                key='key2',
                values=list('abc')
            ),
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

        assert validator.no_errors
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

        assert not validator.no_errors
        assert len(validator.results) == 3
