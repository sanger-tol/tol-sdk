# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime

from sqlalchemy import create_engine, delete
from sqlalchemy.exc import ProgrammingError

from tol.core import DataSource, core_data_object
from tol.sql import (
    create_session_factory,
    create_sql_datasource
)

from .base import DataSourceFixture
from ..types import ALL_MODELS, Related, Root


DB_URI = os.environ['DB_URI']
session_factory = create_session_factory(DB_URI)


class SqlFixture(DataSourceFixture):
    """A `DataSourceFixture` for `SqlDataSource`"""

    def __init__(self) -> None:
        engine = create_engine(DB_URI)
        for model in ALL_MODELS:
            try:
                model.__table__.create(engine)
            except ProgrammingError:
                continue

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
        # need this in case a previous test
        # fails to teardown properly
        self.__delete_all()

        self.__insert_archetypes()

    def after_test(self) -> None:
        self.__delete_all()

    def __delete_all(self) -> None:
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
