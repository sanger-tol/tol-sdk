# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core import Validator


@pytest.fixture
def mock_validator() -> Validator:
    return create_autospec(
        Validator,
        spec_set=True,
    )


class TestValidatorAdd:

    class _TestValidator(Validator):
        def _validate_object(self, obj):
            raise NotImplementedError()

    def test_add_warning(self) -> None:
        val = self._TestValidator()

        val.add_warning(
            object_id='hello',
            detail='A Warning'
        )

        assert len(val.results) == 1
        assert val.no_errors

    def test_add_error(self) -> None:
        val = self._TestValidator()

        val.add_error(
            object_id='hello',
            detail='A Warning'
        )

        assert len(val.results) == 1
        assert not val.no_errors
