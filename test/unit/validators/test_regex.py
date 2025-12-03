# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import (
    Regex,
    RegexValidator,
)


class TestRegexValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = [
            Regex(
                key='key1',
                regex='[abc]',
            ),
            Regex(
                key='key2',
                regex='[abc][def]?',
            ),
        ]

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

        config = [
            Regex(
                key='key1',
                regex='[abc]'
            ),
            # adds warnings
            Regex(
                key='key2',
                regex='[pqr][xyz]',
                is_error=False,
            ),
        ]

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

        config = [
            Regex(
                key='key1',
                regex='[abc]'
            ),
            # adds errors
            Regex(
                key='key2',
                regex='[pqr][xyz]',
            ),
        ]

        validator = RegexValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
