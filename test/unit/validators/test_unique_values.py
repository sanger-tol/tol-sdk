# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import UniqueValuesValidator


class TestUniqueValuesValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        validator = UniqueValuesValidator(
            ['key1']
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

        validator = UniqueValuesValidator(
            ['key3'],
            is_error=False,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert validator.has_no_errors
        assert len(validator.results) == 1

    def test_errors(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        validator = UniqueValuesValidator(
            ['key3'],
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 1
