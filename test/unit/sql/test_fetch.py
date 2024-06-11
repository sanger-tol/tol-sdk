# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core.relationship import RelationshipConfig
from tol.sql import SqlDataSource
from tol.sql.database import Database
from tol.sql.filter import DatabaseFilter
from tol.sql.sort import DatabaseSorter
from tol.sql.sql_converter import (
    DataObjectConverter,
    ModelConverter
)


@pytest.fixture(scope='function')
def db() -> Database:
    return create_autospec(
        Database,
        spec_set=True
    )


@pytest.fixture(scope='module')
def type_tablename_map() -> dict[str, str]:
    return {
        t: t
        for t in (
            'r1',
            'r2',
            'r3',
            'r4',
            'r5'
        )
    }


@pytest.fixture(scope='module')
def rel_config(
) -> dict[str, RelationshipConfig]:

    return {
        'r1': RelationshipConfig(
            to_one={'r2_d2': 'r2'}
        )
    }


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
    database: Database,
    type_tablename_map: dict[str, str],
    rel_config: dict[str, RelationshipConfig],
    do_converter: DataObjectConverter,
    model_converter: ModelConverter,
    db_filter: DatabaseFilter,
    db_sorter: DatabaseSorter
) -> SqlDataSource:

    return SqlDataSource(
        database,
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
        self
    ):
        """
        Converter returns objects with relationships
        """
