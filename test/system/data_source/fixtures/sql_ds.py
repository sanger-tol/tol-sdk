# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import os

from sqlalchemy import create_engine, delete
from sqlalchemy.exc import ProgrammingError

from tol.core import DataSource, core_data_object
from tol.sql import (
    create_session_factory,
    create_sql_datasource
)

from .base import DataSourceFixture
from ..types import ALL_MODELS


DB_URI = os.environ['DB_URI']
session_factory = create_session_factory(DB_URI)


class SqlFixture(DataSourceFixture):
    """A `DataSourceFixture` for `SqlDataSource`"""

    def __init__(self) -> None:
        engine = create_engine(DB_URI)
        for model in ALL_MODELS:
            try:
                model.__table__.create(engine)
            except ProgrammingError as e:
                logging.info(e)

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

    def after_test(self) -> None:
        delete_order = list(reversed(ALL_MODELS))

        session = session_factory()
        for model in delete_order:
            session.execute(
                delete(model)
            )
        session.commit()


sql = SqlFixture()
