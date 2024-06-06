# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from sqlalchemy import delete

from tol.core import DataSource, core_data_object
from tol.sql import create_sql_datasource

from .base import DataSourceFixture
from ..services.sql import (
    DB_URI,
    create_tables,
    session_factory
)
from ..types import ALL_MODELS, Related, Root



class SqlFixture(DataSourceFixture):
    """A `DataSourceFixture` for `SqlDataSource`"""

    def __init__(self) -> None:
        create_tables()

    @property
    def name(self) -> str:
        return 'sql'

    def get_ds_instance(self) -> DataSource:
        sql_ds = create_sql_datasource(
            ALL_MODELS,
            DB_URI
        )
        core_data_object(sql_ds)
        return sql_ds

    def before_test(self) -> None:
        self.__insert_archetypes()

    def after_test(self) -> None:
        delete_order = list(reversed(ALL_MODELS))

        session = session_factory()
        for model in delete_order:
            session.execute(
                delete(model)
            )
        session.commit()

    def __insert_archetypes(self) -> None:
        with session_factory() as sess:
            sess.add(
                Related(
                    id='#REL',
                    str_column='abc',
                    int_column=42,
                    datetime_column=datetime(2021, 1, 1, 0, 0, 0),
                    bool_column=True,
                    list_column=['item']
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
                    related_fkey='#REL'
                )
            )
            sess.commit()


sql = SqlFixture()
