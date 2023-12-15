# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import os
from datetime import datetime

from sqlalchemy import create_engine, delete
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Mapped, mapped_column

from tol.core import DataSource
from tol.sql import (
    create_session_factory,
    create_sql_datasource,
    model_base
)

from .base import DataSourceFixture


DB_URI = os.environ['DB_URI']
session_factory = create_session_factory(DB_URI)


ModelBase = model_base()  # noqa


class Root(ModelBase):
    """
    The Root `ModelBase` child.

    Has `object_type="root"`
    """

    __tablename__ = 'root'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    str_column: Mapped[str] = mapped_column()
    int_column: Mapped[int] = mapped_column()
    datetime_column: Mapped[datetime] = mapped_column()
    bool_column: Mapped[bool] = mapped_column()


models = (
    Root,
)


class SqlFixture(DataSourceFixture):
    """A `DataSourceFixture` for `SqlDataSource`"""

    def __init__(self) -> None:
        engine = create_engine(DB_URI)
        for model in models:
            try:
                model.__table__.create(engine)
            except ProgrammingError as e:
                logging.info(e)

    @property
    def name(self) -> str:
        return 'sql'

    def get_ds_instance(self) -> DataSource:
        return create_sql_datasource(
            models,
            DB_URI
        )

    def after_test(self) -> None:
        delete_order = list(reversed(models))

        session = session_factory()
        for model in delete_order:
            session.execute(
                delete(model)
            )
        session.commit()

    def tear_down(self) -> None:
        pass


sql = SqlFixture()
