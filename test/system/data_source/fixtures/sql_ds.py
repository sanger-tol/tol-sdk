# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime

from tol.core import DataSource, core_data_object
from tol.sql import (
    create_session_factory,
    create_sql_datasource,
)

from .base import DataSourceFixture
from ..types import ALL_MODELS, Related, Root


DB_URI = os.environ['DB_URI']
session_factory = create_session_factory(DB_URI)


class SqlFixture(DataSourceFixture):
    """A `DataSourceFixture` for `SqlDataSource`"""

    @property
    def name(self) -> str:
        return 'sql'

    def get_ds_instance(self) -> DataSource:
        sql_ds = create_sql_datasource(ALL_MODELS, DB_URI)
        core_data_object(sql_ds)
        return sql_ds

    def before_test(self) -> None:
        with session_factory() as sess:
            conn = sess.connection()
            # Drop tables created by previous tests
            Root.metadata.drop_all(conn)
            Root.metadata.create_all(conn)
            sess.commit()
        self.__insert_archetypes()

    def after_test(self) -> None:
        pass

    def __insert_archetypes(self) -> None:
        with session_factory() as sess:
            sess.add(
                Related(
                    id='#REL',
                    str_column='abc',
                    int_column=42,
                    datetime_column=datetime(2021, 1, 1, 0, 0, 0),
                    bool_column=True,
                    list_column=['item'],
                )
            )
            sess.add(
                Root(
                    id='#YOLO',
                    str_column='abc',
                    int_column=42,
                    datetime_column=datetime(2020, 1, 1, 0, 0, 0),
                    bool_column=True,
                    list_column=['item'],
                    related_fkey='#REL',
                )
            )
            sess.commit()


sql = SqlFixture()
