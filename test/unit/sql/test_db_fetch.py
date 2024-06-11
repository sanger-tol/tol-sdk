# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core import DataObject
from tol.core.relationship import (
    RelationshipConfig
)
from tol.sql import SqlDataSource
from tol.sql.database import Database
from tol.sql.filter import DatabaseFilter
from tol.sql.relationship import (
    SqlRelationshipConfig
)
from tol.sql.sort import DatabaseSorter
from tol.sql.sql_converter import (
    DataObjectConverter,
    ModelConverter
)


@pytest.fixture(scope='function')
def db() -> Database:
    mock_db = create_autospec(
        Database,
        spec_set=True
    )
    mock_db.attribute_types = {
        'r1': {},
        'r2': {
            'str_column': str
        }
    }

    return mock_db


@pytest.fixture(scope='module')
def type_tablename_map() -> dict[str, str]:
    return {
        'r1': 'r1',
        'r2': 'r2'
    }


@pytest.fixture(scope='module')
def rel_config(
) -> SqlRelationshipConfig:

    config = create_autospec(
        SqlRelationshipConfig,
        spect_set=True
    )
    config.to_dict.return_value = {
        'r1': RelationshipConfig(
            to_one={'r2_d2': 'r2'}
        )
    }

    return config


@pytest.fixture(scope='function')
def do_converter() -> DataObjectConverter:
    return create_autospec(
        DataObjectConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def model_converter() -> ModelConverter:
    return create_autospec(
        ModelConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def db_filter() -> DatabaseFilter:
    return create_autospec(
        DatabaseFilter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def db_sorter() -> DatabaseSorter:
    return create_autospec(
        DatabaseSorter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def sql_ds(
    db: Database,
    type_tablename_map: dict[str, str],
    rel_config: SqlRelationshipConfig,
    do_converter: DataObjectConverter,
    model_converter: ModelConverter,
    db_filter: DatabaseFilter,
    db_sorter: DatabaseSorter
) -> SqlDataSource:

    return SqlDataSource(
        db,
        type_tablename_map,
        rel_config,
        lambda: model_converter,
        lambda: do_converter,
        lambda: db_filter,
        lambda: db_sorter
    )


class TestFetch:
    """No superfluous fetches"""

    def test_relation(
        self,
        sql_ds: SqlDataSource,
        model_converter: ModelConverter
    ):
        """
        Converter returns objects with relationships
        -> no relation fetch occurs.
        """

        mock_r2 = create_autospec(DataObject, spec_set=True)
        mock_r2.str_column = 'lol'

        mock_r1 = create_autospec(DataObject, spec_set=True)
        mock_r1.type = 'r1'
        mock_r1._to_one_objects = {
            'r2_d2': mock_r2
        }

        model_converter.convert_iterable.return_value = [
            mock_r1
        ]
