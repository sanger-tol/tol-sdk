# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import AllowedValuesValidator


class TestAllowedValuesValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = AllowedValuesValidator.Config(
            field='key1',
            allowed_values=list('abc')
        )

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

        config = AllowedValuesValidator.Config(
            field='key1',
            allowed_values=list('xyz'),
            is_error=False  # adds warnings
        )

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

        config = AllowedValuesValidator.Config(
            field='key1',
            allowed_values=list('xyz'),
            is_error=True  # adds errors
        )

        validator = AllowedValuesValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
