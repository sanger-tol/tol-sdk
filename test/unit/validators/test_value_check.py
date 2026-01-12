# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import ValueCheckValidator


class TestValueCheckValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'SYMBIONT',
        }
        mock_one.SYMBIONT = 'SYMBIONT'

        config = ValueCheckValidator.Config(
            field='SYMBIONT',
            value='SYMBIONT'
        )

        validator = ValueCheckValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one]))
        )
        assert validator.results
