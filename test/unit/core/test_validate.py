# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, ErrorObject, Validator


@pytest.fixture
def mock_validator() -> Validator:
    return create_autospec(
        Validator,
        spec_set=True,
    )


@pytest.fixture
def object_stream(
) -> Iterable[DataObject | ErrorObject]:

    return [
        create_autospec(DataObject),
        ErrorObject({}, 'test'),
    ]


class TestValidator:

    def test_validate(
        self,
        mock_validator: Validator,
        object_stream: Iterable[DataObject | ErrorObject],
    ) -> None:

        results = list(
            Validator.validate(mock_validator, object_stream)
        )

        assert len(results) == 2

        # called only on the `DataObject`, ignoring error ones
        mock_validator._validate_data_object.assert_called_once_with(
            object_stream[0],
        )

    def test_validate_empty_stream(
        self,
        mock_validator: Validator,
    ) -> None:

        results = list(
            Validator.validate(mock_validator, [])
        )

        assert results == []
        mock_validator._validate_data_object.assert_not_called()


class TestValidatorAdd:

    class _TestValidator(Validator):
        def _validate_data_object(self, obj):
            raise NotImplementedError()

    def test_add_warning(self) -> None:
        val = self._TestValidator()

        val.add_warning(
            object_id='hello',
            detail='A Warning'
        )

        assert len(val.results) == 1
        assert val.has_no_errors

    def test_add_error(self) -> None:
        val = self._TestValidator()

        val.add_error(
            object_id='hello',
            detail='A Warning'
        )

        assert len(val.results) == 1
        assert not val.has_no_errors
