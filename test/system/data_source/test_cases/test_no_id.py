# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import OperableDataSource

from ..dec import against
from ..fixtures.api.sql import api_sql
from ..fixtures.sql_ds import sql


class TestNoID:
    """
    An `autoincrement=True` ID doesn't need to be specified
    for `(api ->) sql`
    """

    @against(sql, api_sql)
    def test_insert(self, data_source: OperableDataSource, ds_sleep):
        obj = data_source.data_object_factory('inc')
        returned = list(
            data_source.insert('inc', [obj])
        )
        assert returned[0].id is not None

    @against(sql, api_sql)
    def test_upsert(self, data_source: OperableDataSource, ds_sleep):
        obj = data_source.data_object_factory('inc')
        returned = list(
            data_source.upsert('inc', [obj])
        )
        assert returned[0].id is not None
