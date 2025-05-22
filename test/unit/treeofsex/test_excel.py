# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from unittest.mock import create_autospec

import pytest

from tol.core import (
    DataObject,
    DataObjectFactory,
)
from tol.treeofsex.excel import TOSEmitter


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'test_indeed'


@pytest.fixture
def data_object_factory(
    object_type: str,
) -> DataObjectFactory:
    """Returns the given ID only."""

    factory = create_autospec(
        DataObjectFactory,
        spec_set=True,
    )

    def __make(
        type_: str,
        id_: str | None = None,
        *args,
        **kwargs,
    ) -> DataObject:

        assert type_ == object_type

        return id_


class TestTOSEmitter:

    def test_emit(
        self,
        data_object_factory: DataObjectFactory,
    ) -> None:
        """
        Using a real spreadsheet, with an offset in
        both row and column.
        """

        sheet_path = BASE_DIR / 'objects.xlsx'

        emitter = TOSEmitter(
            data_object_factory,
            sheet_path,
            column_offset=2,
            row_offset=3,
        )

        expected = list(
            range(2, 5)
        )

        observed = list(
            emitter.emit()
        )

        assert observed == expected

