# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy.orm import Session as SqlaSession

from ..core.session import DataSourceSession

if typing.TYPE_CHECKING:
    from .sql_datasource import SqlDataSource


class SqlDataSourceSession(DataSourceSession):

    def __init__(
        self,
        data_source: SqlDataSource
    ) -> None:

        self.__session = data_source.create_sqla_session()

        super().__init__(data_source)

    def __exit__(self, type_, value, tb) -> None:
        self.__session.close()

        super().__exit__(type_, value, tb)

    @property
    def _sqla_session(self) -> SqlaSession:
        """The underlying `sqlalchemy.orm.Session`."""

        return self.__session
