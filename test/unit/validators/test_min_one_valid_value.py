# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import (
    MinOneValidValueValidator
)


class TestMinOneValidValueValidator:

    def test_no_results(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = MinOneValidValueValidator.Config(
            blank_values=['', 'NA', 'N/A'],
            keys=['key1', 'key2'],
        )

        validator = MinOneValidValueValidator(
            config,
        )

        list(
            validator.validate(mock_objs)
        )

        assert not validator.results

    def test_errors(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        config = MinOneValidValueValidator.Config(
            blank_values=['a', 'b', 'c'],
            keys=['key1', 'key2'],
        )

        validator = MinOneValidValueValidator(
            config,
        )

        list(
            validator.validate(mock_objs)
        )

        assert not validator.warnings
        assert len(validator.errors) == 3
