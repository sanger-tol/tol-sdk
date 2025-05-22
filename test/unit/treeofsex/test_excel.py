# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from unittest.mock import create_autospec

import pytest

from tol.core import (
    DataObjectFactory,
    DataSource,
    core_data_object,
)
from tol.treeofsex.excel import TOSEmitter


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'test_indeed'


@pytest.fixture(scope='module')
def type_mapping() -> dict[str, str]:
    return {
        'int_column': 'int',
        'str_column': 'str',
        'bool_column': 'bool',
        'datetimecolumn': 'datetime',
        'float_column': 'float',
    }


@pytest.fixture
def mock_ds(object_type: str) -> DataSource:
    __ds: DataSource = create_autospec(
        DataSource,
        spec_set=True,
    )

    __ds.supported_types = [object_type]

    return __ds


@pytest.fixture
def data_object_factory(mock_ds) -> DataObjectFactory:
    """Returns the given ID only."""

    return core_data_object(mock_ds)


class TestTOSEmitter:

    def test_emit(
        self,
        data_object_factory: DataObjectFactory,
        object_type: str,
        type_mapping: dict[str, str],
    ) -> None:
        """
        Using a real spreadsheet, with an offset in
        both row and column.
        """

        sheet_path = BASE_DIR / 'objects.xlsx'

        emitter = TOSEmitter(
            data_object_factory,
            sheet_path,
            'Sheet1',
            object_type=object_type,
            type_mapping=type_mapping,
        )

        observed = list(emitter)
        import logging; logging.error(observed[0].attributes); assert False

