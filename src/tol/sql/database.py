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
    def delete(
        self,
        tablename: str,
        instance_id: Any,
        user_id: Optional[str] = None
    ) -> None:
        """
        Deletes the `Model` instance of specified tablename and
        instance-ID.
        """

    @abstractmethod
    def upsert(
        self,
        instance: Model,
        user_id: Optional[str] = None
    ) -> None:
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

    @property
    @abstractmethod
    def attribute_types(self) -> dict[str, dict[str, type]]:
        """
        The mapping of attribute name to type for each model under
        this `Database` instance.
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
        self.__attribute_types = self.__get_attribute_types()

    def get_by_id(self, tablename: str, instance_id: Any) -> Optional[Model]:
        result = self.__get_instance_by_id(tablename, instance_id)
        return result

    def get_page(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[DatabaseSorter] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Iterable[Model]:

        _, query = self.__get_model_query(tablename)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        if sort_by is not None:
            query = sort_by.sort(query, tablename, self.__tablename_model_dict)
        query = query.limit(limit).offset(offset)
        results = query.all()
        return results

    def count(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter] = None
    ) -> int:

        _, query = self.__get_model_query(tablename)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        count = query.count()
        return count

    def delete(
        self,
        tablename: str,
        instance_id: Any,
        user_id: Optional[str] = None
    ) -> None:
        instance = self.__get_instance_by_id(tablename, instance_id)
        session = self.__session_factory()
        session.delete(instance)
        self.__commit_session(
            session,
            instance,
            'deletion',
            user_id=user_id,
            is_delete=True
        )

    def upsert(
        self,
        instance: Model,
        user_id: Optional[str] = None
    ) -> None:

        session = self.__upsert_to_session(instance)
        self.__commit_session(
            session,
            instance,
            'upserting',
            user_id=user_id
        )

    def get_to_one_relation(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Optional[Model]:

        instance = self.__get_instance_by_id(tablename, instance_id)
        result = instance.instance_to_one_relations[relationship_name]
        return result

    def get_to_many_relations(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str
    ) -> Iterable[Model]:

        instance = self.__get_instance_by_id(tablename, instance_id)
        result = instance.instance_to_many_relations[relationship_name]
        return result

    @property
    def attribute_types(self) -> dict[str, dict[str, type]]:
        return self.__attribute_types

    def __get_attribute_types(self) -> dict[str, dict[str, type]]:
        return {
            t: m.get_attribute_types()
            for t, m in self.__tablename_model_dict.items()
        }

    def __get_model_query(
        self,
        tablename: str
    ) -> Tuple[Type[Model], Query]:

        model = self.__tablename_model_dict[tablename]
        session = self.__session_factory()
        query = session.query(model)
        return model, query

    def __commit_session(
        self,
        session: Session,
        instance: Model,
        operation: str,
        user_id: Optional[str] = None,
        is_delete: bool = False
    ) -> None:

        try:
            if not is_delete:
                self.__before_commit(instance, session, user_id)
            session.commit()
        except IntegrityError:
            self.__raise_integrity_error(instance, operation)

    def __before_commit(
        self,
        instance: Model,
        session: Session,
        user_id: Optional[str]
    ) -> None:
        instance.before_commit(user_id=user_id)
        session.merge(instance)

    def __get_instance_by_id(
        self,
        tablename: str,
        instance_id: str
    ) -> Optional[Model]:
        """
        Gets an instance by its tablename and id. Returns a session object that
        must be manually closed.
        """

        model, query = self.__get_model_query(tablename)
        id_column = getattr(model, model.get_id_column_name())
        result = query.filter(id_column == instance_id).one_or_none()
        return result

    def __get_tablename_model_dict(
        self,
        models: List[Type[Model]]
    ) -> Dict[str, Type[Model]]:

        return {
            m.get_table_name(): m for m in models
        }

    def __upsert_to_session(self, instance: Model) -> Session:
        old_instance = self.__get_instance_by_id(
            instance.get_table_name(),
            instance.instance_id
        )
        session = self.__session_factory()
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
