# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import SymbiontCheckValidator


class TestSymbiontCheckValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'SYMBIONT',
        }
        mock_one.SYMBIONT = 'SYMBIONT'
        mock_one.SPECIMEN_ID = 'one'

        config = SymbiontCheckValidator.Config(
            symbiont_field='SYMBIONT',
        )

        validator = SymbiontCheckValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one]))
        )
        assert validator.results
