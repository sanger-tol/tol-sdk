# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import AllowedKeysValidator


class TestAllowedKeysValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = AllowedKeysValidator.Config(
            allowed_keys=['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7'],
        )

        validator = AllowedKeysValidator(
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

        config = AllowedKeysValidator.Config(
            allowed_keys=['key1', 'key3', 'key4', 'key5', 'key6', 'key7'],
            is_error=False,
        )

        validator = AllowedKeysValidator(
            config
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

        config = AllowedKeysValidator.Config(
            allowed_keys=['key2', 'key3', 'key4', 'key5', 'key6', 'key7'],
        )

        validator = AllowedKeysValidator(
            config
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
