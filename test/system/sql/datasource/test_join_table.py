# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

import pytest

from tol.core import core_data_object
from tol.core.datasource_filter import AndFilter
from tol.core.relationship import RelationshipConfig
from tol.sql import SqlDataSource, create_sql_datasource
from tol.sql.database import DefaultDatabase
from tol.sql.filter import DatabaseFilter, DefaultDatabaseFilter
from tol.sql.relationship import SqlRelationshipConfig

from .. import models


@pytest.fixture
def sql_ds(db_uri: str, models_list) -> SqlDataSource:
    ds = create_sql_datasource(
        models_list,
        db_uri
    )
    core_data_object(ds)

    return ds


class TestJoinTable:
    """
    Join Tables do not require a special, separate serial
    Primary Key. They can use the two foreign keys as
    a compound PK.
    """

    def test_basic(self, sql_ds: SqlDataSource):
        r6 = sql_ds.data_object_factory(
            'r6',
            id_='r6_ID'
        )
        sql_ds.insert('r6', [r6])

        r7 = sql_ds.data_object_factory(
            'r7',
            id_='r7_ID'
        )
        sql_ds.insert('r7', [r7])

        r6_to_r7 = sql_ds.data_object_factory(
            'r6_r7',
            to_one={
                'r6_rel': r6,
                'r7_rel': r7
            }
        )
        sql_ds.insert('r6_r7', [r6_to_r7])

        joiner = sql_ds.get_one('r6_r7', 'r6:r7')

        assert joiner.r6_rel.id == 'r6'
        assert joiner.r7_rel.id == 'r7'
