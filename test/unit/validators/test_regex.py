# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import (
    RegexValidator,
)


class TestRegexValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = RegexValidator.Config(
            regexes=[
                {'key': 'key1', 'regex': '[abc]'},
                {'key': 'key2', 'regex': '[abc][def]?'},
            ]
        )

        validator = RegexValidator(
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

        config = RegexValidator.Config(
            regexes=[
                {'key': 'key1', 'regex': '[abc]'},
                # adds warnings
                {'key': 'key2', 'regex': '[pqr][xyz]', 'is_error': False},
                # tests none value
                {'key': 'key6', 'regex': 'present'},
            ]
        )

        validator = RegexValidator(
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

        config = RegexValidator.Config(
            regexes=[
                {'key': 'key1', 'regex': '[abc]'},
                # adds errors
                {'key': 'key2', 'regex': '[pqr][xyz]'},
            ]
        )

        validator = RegexValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
