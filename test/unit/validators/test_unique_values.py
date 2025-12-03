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

        config = UniqueValuesValidator.Config(
            unique_keys=['key1']
        )

        validator = UniqueValuesValidator(
            config
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

        config = UniqueValuesValidator.Config(
            unique_keys=['key3'],
            is_error=False,
        )

        validator = UniqueValuesValidator(
            config
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

        config = UniqueValuesValidator.Config(
            unique_keys=['key3'],
        )

        validator = UniqueValuesValidator(
            config
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 1

    def test_multiple_keys_pass(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = UniqueValuesValidator.Config(
            unique_keys=[['key1', 'key2'], ['key3', 'key2']],
        )

        validator = UniqueValuesValidator(
            config
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert not validator.errors

    def test_multiple_keys_error(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = UniqueValuesValidator.Config(
            unique_keys=[['key3', 'key4']],
            is_error=True,
        )

        validator = UniqueValuesValidator(
            config
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 1
