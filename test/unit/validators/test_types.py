# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import TypesValidator


class TestTypesValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = TypesValidator.Config(
            allowed_types={
                'key1': 'str',
                'key2': 'str',
                'key3': 'str',
                'key4': 'str',
                'key5': 'str',
                'key6': 'str',
                'key7': 'list',
                'key8': 'datetime',
                'key9': 'float',
                'key10': 'bool',
                'key11': 'int',
                'key12': 'time',
            },
        )

        validator = TypesValidator(
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

        config = TypesValidator.Config(
            allowed_types={
                'key1': 'int',
                'key2': 'str',
                'key3': 'str',
                'key4': 'str',
                'key5': 'str',
                'key6': 'str',
                'key7': 'list',
                'key8': 'datetime',
                'key9': 'float',
                'key10': 'bool',
                'key11': 'int',
                'key12': 'time',
            },
            is_error=False,
        )

        validator = TypesValidator(
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

        config = TypesValidator.Config(
            allowed_types={
                'key1': 'int',
                'key2': 'int',
                'key3': 'datetime',
                'key4': 'int',
                'key5': 'int',
                'key6': 'int',
                'key7': 'str',
                'key8': 'float',
                'key9': 'bool',
                'key10': 'int',
                'key11': 'time',
                'key12': 'str',
            }
        )

        validator = TypesValidator(
            config
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 35  # One of the values is None, which is skipped
