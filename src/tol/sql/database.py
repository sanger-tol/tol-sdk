# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy.orm import Query, Session

from .filter import DatabaseFilter
from .model import Model
from .session import SessionFactory


class Database(ABC):
    """Encapsulates basic operations on a Database"""

    @abstractmethod
    def get_by_id(self, tablename: str, instance_id: Any) -> Optional[Model]:
        """
        Gets a single instance by its instance-ID, or None if not found.

        Note that this "instance-ID" may not always be named "id" on the
        Model class.
        """

    @abstractmethod
    def get_list(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Iterable[Model]:
        """
        Returns an Iterable of Model instances according
        to the given filters, offset, and limit.
        """

    @abstractmethod
    def count(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None
    ) -> int:
        """
        Counts the total number of Model instances of the given
        tablename matching the given filters.
        """


class DefaultDatabase(Database):
    """A reasonable-default implementation of the Database ABC."""

    def __init__(
        self,
        session_factory: SessionFactory,
        models: List[Type[Model]]
    ) -> None:
        self.__session_factory = session_factory
        self.__tablename_model_dict = self.__get_tablename_model_dict(models)

    def get_by_id(self, tablename: str, instance_id: Any) -> Optional[Model]:
        model, session, query = self.__get_model_session_query(tablename)
        id_column = getattr(model, model.get_id_column_name())
        result = query.filter(id_column == instance_id).one_or_none()
        session.close()
        return result

    def get_list(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Iterable[Model]:
        _, session, query = self.__get_model_session_query(tablename)
        query = query.limit(limit).offset(offset)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        results = query.all()
        session.close()
        return results

    def count(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None
    ) -> int:
        _, session, query = self.__get_model_session_query(tablename)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        count = query.count()
        session.close()
        return count

    def __get_model_session_query(
        self,
        tablename: str
    ) -> Tuple[Type[Model], Session, Query]:

        model = self.__tablename_model_dict[tablename]
        session = self.__session_factory()
        query = session.query(model)
        return model, session, query

    def __get_tablename_model_dict(
        self,
        models: List[Type[Model]]
    ) -> Dict[str, Type[Model]]:

        return {
            m.get_table_name(): m for m in models
        }
