# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from datetime import datetime
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

        obj1, obj2 = list(emitter)

        assert obj1.type == object_type
        assert obj1.id == '1'
        dt2 = obj1.attributes.pop('datetime_column')
        assert obj1.attributes == {
            'bool_column': True,
            'float_column': 42.0,
            'int_column': 42,
            'str_column': 'hello',
        }
        assert dt2 == datetime(
            year=2000,
            month=2,
            day=18,
        )

        assert obj2.type == object_type
        assert obj2.id == '2'
        dt2 = obj2.attributes.pop('datetime_column')
        assert obj2.attributes == {
            'bool_column': False,
            'float_column': 9032.2,
            'int_column': 9093,
            'str_column': 'world',
        }
        assert dt2 == datetime(
            year=2010,
            month=2,
            day=18,
        )
