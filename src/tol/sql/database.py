# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Type

from sqlalchemy import distinct, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import MappedColumn, Query, Session, joinedload
from sqlalchemy.orm.attributes import flag_modified

from .filter import DatabaseFilter
from .model import Model
from .session import SessionFactory
from .sort import DatabaseSorter
from ..core import DataSourceError


class Database(ABC):
    """Encapsulates basic operations on a Database"""

    @abstractmethod
    def get_by_id(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        requested_relationships: dict[str, str] | None = None,
    ) -> Optional[Model]:
        """
        Gets a single instance by its instance-ID, or None if not found.

        Note that this "instance-ID" may not always be named "id" on the
        `Model` class.
        """

    @abstractmethod
    def get_page(
        self,
        tablename: str,
        in_session: Session,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[DatabaseSorter] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        requested_relationships: dict[str, str] | None = None
    ) -> Iterable[Model]:
        """
        Returns an Iterable of `Model` instances according
        to the given filters, offset, and limit.
        """

    @abstractmethod
    def count(
        self,
        tablename: str,
        in_session: Session,
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
        in_session: Session,
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
        in_session: Session,
        user_id: Optional[str] = None
    ) -> Model:
        """Performs an "upsert" on the given `Model` instance."""

    @abstractmethod
    def insert(
        self,
        instance: Model,
        in_session: Session,
        user_id: Optional[str] = None
    ) -> Model:
        """
        "Inserts" the given `Model` instance.

        Must not already exist.
        """

    @abstractmethod
    def get_to_one_relation(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str,
        in_session: Session
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
        relationship_name: str,
        in_session: Session
    ) -> Iterable[Model]:
        """
        For the instance of given tablename and ID, gets the to-many
        instances under the given relationship.
        """

    @abstractmethod
    def get_group_stats(
        self,
        tablename: str,
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
        in_session: Session,
        filters: DatabaseFilter | None = None,
    ) -> list[dict[str, dict[str, Any]]]:
        """
        Provides the specified `stats`:

        - grouped by the cartesian product of unique tuples
          under `group_by`
        - on the fields specified in `stats_fields`
        """

    @property
    @abstractmethod
    def attribute_types(self) -> dict[str, dict[str, type]]:
        """
        The mapping of attribute name to type for each model under
        this `Database` instance.
        """

    @property
    @abstractmethod
    def session_factory(self) -> SessionFactory:
        """
        Returns a `Callable` that returns a `Session` instance.
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

    @property
    def session_factory(self) -> SessionFactory:
        return self.__session_factory

    def get_by_id(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        requested_relationships: dict[str, str] | None = None,
    ) -> Optional[Model]:

        result = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session,
            requested_relationships,
        )
        return result

    def get_page(
        self,
        tablename: str,
        in_session: Session,
        filters: Optional[DatabaseFilter] = None,
        sort_by: Optional[DatabaseSorter] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        requested_relationships: dict[str, str] | None = None,
    ) -> Iterable[Model]:

        _, query = self.__get_model_query(
            tablename,
            in_session,
            requested_relationships
        )
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
        in_session: Session,
        filters: Optional[DatabaseFilter] = None
    ) -> int:

        _, query = self.__get_model_query(tablename, in_session, None)
        if filters is not None:
            query = filters.filter(query, tablename, self.__tablename_model_dict)
        count = query.count()
        return count

    def delete(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        user_id: Optional[str] = None
    ) -> None:

        instance = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session
        )
        in_session.delete(instance)
        return self.__commit_session(
            in_session,
            instance,
            'deletion',
            user_id=user_id,
            is_delete=True
        )

    def upsert(
        self,
        instance: Model,
        in_session: Session,
        user_id: Optional[str] = None
    ) -> Model:

        instance = self.__upsert_to_session(
            instance,
            in_session
        )
        in_session.flush()
        return self.__commit_session(
            in_session,
            instance,
            'upserting',
            user_id=user_id
        )

    def insert(
        self,
        instance: Model,
        in_session: Session,
        user_id: Optional[str] = None,
    ) -> Model:

        in_session.add(instance)

        return self.__commit_session(
            in_session,
            instance,
            'inserting',
            user_id=user_id
        )

    def get_to_one_relation(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str,
        in_session: Session,
    ) -> Optional[Model]:

        instance = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session
        )
        result = instance.instance_to_one_relations[relationship_name]
        return result

    def get_to_many_relations(
        self,
        tablename: str,
        instance_id: str,
        relationship_name: str,
        in_session: Session
    ) -> Iterable[Model]:

        instance = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session
        )
        result = instance.instance_to_many_relations[relationship_name]
        return result

    def get_group_stats(
        self,
        tablename: str,
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
        in_session: Session,
        filters: DatabaseFilter | None = None,
    ) -> list[dict[str, dict[str, Any]]]:

        model, query = self.__get_model_query(
            tablename,
            in_session,
            None,
        )

        query = self.__filter_query(query, tablename, filters)
        query, s_columns = self.__apply_stats(
            query,
            filters,
            model,
            stats_fields,
            stats,
        )
        query, g_columns = self.__apply_group_by(
            query,
            model,
            group_by,
            filters,
        )

        return self.__get_stats_from_query(
            query,
            group_by,
            stats_fields,
            stats,
            g_columns,
            s_columns,
        )

    @property
    def attribute_types(self) -> dict[str, dict[str, type]]:
        return self.__attribute_types

    def __get_stats_from_query(
        self,
        query: Query,
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
        group_by_columns: list[MappedColumn],
        stat_columns: list[MappedColumn],
    ) -> list[dict[str, dict[str, Any]]]:

        query = query.with_entities(
            *group_by_columns,
            *stat_columns,
        )
        results = query.all()

        return self.__parse_results(
            results,
            group_by,
            stats_fields,
            stats,
        )

    def __parse_results(
        self,
        results: list[list[Any]],
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
    ) -> list[dict[str, dict[str, Any]]]:

        return [
            self.__parse_row(
                r,
                group_by,
                stats_fields,
                stats,
            )
            for r in results
        ]

    def __parse_row(
        self,
        result: list[Any],
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
    ) -> dict[str, dict[str, Any]]:

        group_keys = self.__parse_group_keys(
            result,
            group_by,
        )
        stats_dict = self.__parse_stats_dict(
            result,
            group_by,
            stats_fields,
            stats,
        )

        return {
            'key': group_keys,
            'stats': stats_dict,
        }

    def __parse_stats_dict(
        self,
        result: list[Any],
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
    ) -> dict[str, Any]:

        stats_dict = {}

        num_stats = len(stats)
        stats_values = result[len(group_by):]

        for i, field in enumerate(stats_fields):
            values = stats_values[i * num_stats:(i + 1) * num_stats]
            values_dict = dict(zip(stats, values))
            stats_dict[field] = values_dict

        stats_dict['count'] = stats_values[-1]

        return stats_dict

    def __parse_group_keys(
        self,
        result: list[Any],
        group_by: list[str],
    ) -> dict[str, Any]:

        group_values = result[:len(group_by)]

        return dict(zip(group_by, group_values))

    def __apply_stats(
        self,
        query: Query,
        filters: DatabaseFilter,
        model: type[Model],
        stats_fields: list[str],
        stats: list[str],
    ) -> tuple[Query, list[MappedColumn]]:

        stat_columns = []

        for field in stats_fields:
            column, query = self.__get_column(
                model,
                filters,
                field,
                query,
            )
            stat_columns.extend(
                self.__apply_stats_for_field(
                    column,
                    stats,
                )
            )

        stat_columns.append(func.count())

        return query, stat_columns

    def __apply_stats_for_field(
        self,
        column: MappedColumn,
        stats: list[str],
    ) -> list[Any]:

        return [
            self.__get_stat_clause(
                column,
                stat,
            )
            for stat in stats
        ]

    def __get_column(
        self,
        model: type[Model],
        filters: DatabaseFilter,
        field: str,
        query: Query
    ) -> tuple[MappedColumn, Query]:

        column = filters.get_column(model, field)
        if '.' in field:
            query = filters.apply_joins_on_query(
                query,
                [column],
            )

        return column, query

    def __get_stat_clause(
        self,
        column: MappedColumn,
        stat: str,
    ) -> Any:

        if stat == 'min':
            return func.min(column)
        elif stat == 'max':
            return func.max(column)
        elif stat == 'sum':
            # don't try to sum datetimes
            if column.type.python_type not in [int, float]:
                return None
            return func.sum(column)
        elif stat == 'unique':
            return func.count(distinct(column))

    def __apply_group_by(
        self,
        query: Query,
        model: type[Model],
        group_by: list[str],
        filters: DatabaseFilter,
    ) -> tuple[Query, list[MappedColumn]]:
        """Must be done last in `get_group_stats()`."""

        g_columns = []

        for g in group_by:
            g_column, query = self.__get_column(
                model,
                filters,
                g,
                query
            )
            g_columns.append(g_column)

        return query.group_by(*g_columns).order_by(*g_columns), g_columns

    def __filter_query(
        self,
        query: Query,
        tablename: str,
        filters: DatabaseFilter | None,
    ) -> Query:

        if filters:
            query = filters.filter(
                query,
                tablename,
                self.__tablename_model_dict,
            )

        return query

    def __get_attribute_types(self) -> dict[str, dict[str, type]]:
        return {
            t: m.get_attribute_types()
            for t, m in self.__tablename_model_dict.items()
        }

    def __get_model_query(
        self,
        tablename: str,
        in_session: Session,
        requested_relationships: dict | None,
    ) -> tuple[Type[Model], Query]:

        model = self.__tablename_model_dict[tablename]
        query = in_session.query(model)

        if requested_relationships:
            query = self.__apply_requested_relationships(
                query,
                requested_relationships
            )

        return model, query

    def __apply_requested_relationships(
        self,
        query: Query,
        requested_relationships: dict[str, str]
    ) -> Query:

        tablename = requested_relationships.pop('__tablename__')
        if not requested_relationships:
            return query

        model = self.__tablename_model_dict[tablename]

        for r_name, r_dict in requested_relationships.items():
            relationship = getattr(model, r_name)
            query.options(
                joinedload(relationship)
            )

            query = self.__apply_requested_relationships(query, r_dict)

        return query

    def __commit_session(
        self,
        in_session: Session,
        instance: Model,
        operation: str,
        user_id: Optional[str] = None,
        is_delete: bool = False
    ) -> Model | None:

        try:
            if not is_delete:
                self.__before_commit(instance, in_session, user_id)
            in_session.commit()
            if not is_delete:
                in_session.refresh(instance)
                return instance
        except IntegrityError:
            in_session.rollback()
            self.__raise_integrity_error(instance, operation)

    def __before_commit(
        self,
        instance: Model,
        in_session: Session,
        user_id: Optional[str]
    ) -> None:

        instance.before_commit(user_id=user_id)
        in_session.merge(instance)

    def __get_instance_by_id(
        self,
        tablename: str,
        instance_id: str,
        in_session: Session,
        requested_relationships: dict[str, str] | None = None,
    ) -> Optional[Model]:
        """
        Gets an instance by its tablename and id.
        """

        model, query = self.__get_model_query(
            tablename,
            in_session,
            requested_relationships
        )
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

    def __upsert_to_session(
        self,
        instance: Model,
        in_session: Session
    ) -> Model:

        old_instance = self.__get_instance_by_id(
            instance.get_table_name(),
            instance.instance_id,
            in_session
        )
        if old_instance is not None:
            instance = self.__handle_difference(
                old_instance,
                instance
            )
            in_session.flush()
            return instance

        in_session.add(instance)
        return instance

    def __handle_difference(self, old: Model, new: Model) -> Model:
        """
        Performs various pre-merge operations, including:

        - merging `list`s and `dict`s like `ElasticDataSource`.
        """

        self.__handle_diff_dict(old, new)
        self.__handle_diff_list(old, new)

        __keys = [
            *new.get_attribute_types(),
            *new.get_all_foreign_key_names()
        ]

        for k in __keys:
            new_val = getattr(new, k)
            if self.__ignore_new_val(new, k, new_val):
                continue
            setattr(old, k, new_val)

        return old

    def __ignore_new_val(
        self,
        instance: Model,
        k: str,
        v: Any
    ) -> bool:

        """
        Returns `True` if the value is both:

        - equal to `None`
        - not previously directly set on the Model
        """

        return v is None and not self.__explititly_set(
            instance,
            k
        )

    def __explititly_set(
        self,
        instance: Model,
        k: str
    ) -> bool:

        if not hasattr(instance, '_sa_instance_state'):
            return False

        return k in instance._sa_instance_state.dict

    def __handle_diff_list(self, old: Model, new: Model) -> None:
        for k in self.__get_type_column_keys(new, list):
            merge_list = getattr(old, k, [])
            if merge_list is None:
                continue

            new_list = getattr(new, k, [])

            for el in new_list:
                if el not in merge_list:
                    merge_list.append(el)

            setattr(new, k, merge_list)

            flag_modified(old, k)

    def __handle_diff_dict(self, old: Model, new: Model) -> None:
        for k in self.__get_type_column_keys(new, dict):
            merge_dict = getattr(old, k, {})
            if merge_dict is None:
                continue

            new_dict = getattr(new, k, {})

            setattr(
                new,
                k,
                merge_dict | new_dict
            )

            flag_modified(old, k)

    def __get_type_column_keys(
        self,
        instance: Model,
        type_: type[Any]
    ) -> list[str]:

        return [
            k for k in instance.get_attribute_types().keys()
            if self.__is_type(instance, k, type_)
        ]

    def __is_type(
        self,
        instance: Model,
        key: str,
        type_: type[Any]
    ) -> bool:

        value = getattr(instance, key)
        return isinstance(value, type_)

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
