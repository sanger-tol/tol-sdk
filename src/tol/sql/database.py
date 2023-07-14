# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from .filter import DatabaseFilter
from .model import Model
from .session import SessionFactory
from .sort import DatabaseSorter
from ..core import DataSourceError


class Database(ABC):
    """Encapsulates basic operations on a Database"""

    @abstractmethod
    def get_by_id(self, tablename: str, instance_id: Any) -> Optional[Model]:
        """
        Gets a single instance by its instance-ID, or None if not found.

        Note that this "instance-ID" may not always be named "id" on the
        `Model` class.
        """

    @abstractmethod
    def get_page(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[DatabaseSorter] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Iterable[Model]:
        """
        Returns an Iterable of `Model` instances according
        to the given filters, offset, and limit.
        """

    @abstractmethod
    def count(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None
    ) -> int:
        """
        Counts the total number of `Model` instances of the given
        tablename matching the given filters.
        """

    @abstractmethod
    def delete(self, tablename: str, instance_id: Any) -> None:
        """
        Deletes the `Model` instance of specified tablename and
        instance-ID.
        """

    @abstractmethod
    def upsert(self, instance: Model) -> None:
        """Performs an "upsert" on the given `Model` instance."""

    @abstractmethod
    def get_to_one_relation(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Optional[Model]:
        """
        For the instance of given tablename and ID, gets the to-one
        instance under the given relationship.
        """

    @abstractmethod
    def get_to_many_relations(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Iterable[Model]:
        """
        For the instance of given tablename and ID, gets the to-many
        instances under the given relationship.
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
        result, session = self.__get_instance_by_id(tablename, instance_id)
        session.close()
        return result

    def get_page(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[DatabaseSorter] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Iterable[Model]:

        _, session, query = self.__get_model_session_query(tablename)
        query = query.limit(limit).offset(offset)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        if sort_by is not None:
            query = sort_by.sort(query, tablename, self.__tablename_model_dict)
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

    def delete(self, tablename: str, instance_id: Any) -> None:
        instance, session = self.__get_instance_by_id(tablename, instance_id)
        session.delete(instance)
        self.__commit_session(session, instance, 'deletion')

    def upsert(self, instance: Model) -> None:
        session = self.__upsert_to_session(instance)
        self.__commit_session(session, instance, 'upserting')

    def get_to_one_relation(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Optional[Model]:

        instance, session = self.__get_instance_by_id(tablename, instance_id)
        result = instance.instance_to_one_relations[relationship_name]
        session.close()
        return result

    def get_to_many_relations(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Iterable[Model]:

        instance, session = self.__get_instance_by_id(tablename, instance_id)
        result = instance.instance_to_many_relations[relationship_name]
        session.close()
        return result

    def __get_model_session_query(
        self,
        tablename: str
    ) -> Tuple[Type[Model], Session, Query]:

        model = self.__tablename_model_dict[tablename]
        session = self.__session_factory()
        query = session.query(model)
        return model, session, query

    def __commit_session(
        self,
        session: Session,
        instance: Model,
        operation: str
    ) -> None:

        try:
            session.commit()
        except IntegrityError:
            self.__raise_integrity_error(instance, operation)
        finally:
            session.close()

    def __get_instance_by_id(
        self,
        tablename: str,
        instance_id: str
    ) -> Tuple[Optional[Model], Session]:
        """
        Gets an instance by its tablename and id. Returns a session object that
        must be manually closed.
        """

        model, session, query = self.__get_model_session_query(tablename)
        id_column = getattr(model, model.get_id_column_name())
        result = query.filter(id_column == instance_id).one_or_none()
        return result, session

    def __get_tablename_model_dict(
        self,
        models: List[Type[Model]]
    ) -> Dict[str, Type[Model]]:

        return {
            m.get_table_name(): m for m in models
        }

    def __upsert_to_session(self, instance: Model) -> Session:
        old_instance, session = self.__get_instance_by_id(
            instance.get_table_name(),
            instance.instance_id
        )
        if old_instance is None:
            session.add(instance)
        else:
            session.merge(instance)

        return session

    def __raise_integrity_error(
        self,
        instance: Model,
        operation_name: str
    ) -> None:
        relationship_values = instance.get_to_many_relationship_config().values()
        relationship_names = ', '.join(relationship_values)
        raise DataSourceError(
            title='Database Integrity Error',
            detail=(
                'An integrity error was encountered in the Database during '
                f'{operation_name} of the row with tablename '
                f'"{instance.get_table_name()}" and instance-ID '
                f'"{instance.instance_id}". This is usually due '
                f'to another instance pointing towards this one. '
                f'Hint - check the following tables: "{relationship_names}".'
            )
        )
