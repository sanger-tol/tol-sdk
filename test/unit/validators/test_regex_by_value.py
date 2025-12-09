# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import (
    RegexByValueValidator,
)


class TestRegexByValueValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = RegexByValueValidator.Config(
            key_column='key1',
            regexes={
                'a': [
                    {'key': 'key2', 'regex': '[a]?'},
                    {'key': 'key2', 'regex': '[^z]'},
                ],
                'b': [
                    {'key': 'key2', 'regex': '[b]?'},
                ],
                'c': [
                    {'key': 'key2', 'regex': '[c]?'}
                ],
            },
        )

        validator = RegexByValueValidator(
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

        config = RegexByValueValidator.Config(
            key_column='key1',
            regexes={
                'a': [
                    {'key': 'key2', 'regex': '[a]?'},
                    {'key': 'key2', 'regex': '[^a]', 'is_error': False},
                ],
                'b': [
                    {'key': 'key2', 'regex': '[^b]', 'is_error': False},
                ],
                'c': [
                    {'key': 'key2', 'regex': '[^c]', 'is_error': False},
                ],
            },
        )

        validator = RegexByValueValidator(
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

        config = RegexByValueValidator.Config(
            key_column='key1',
            regexes={
                'a': [
                    {'key': 'key2', 'regex': '[a]?'},
                    {'key': 'key2', 'regex': '[^a]'},
                ],
                'b': [
                    {'key': 'key2', 'regex': '[^b]'},
                ],
                'c': [
                    {'key': 'key2', 'regex': '[^c]'},
                ],
            },
        )

        validator = RegexByValueValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
