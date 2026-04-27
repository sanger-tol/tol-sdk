# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from cachetools.func import ttl_cache

from sqlalchemy import Select, distinct, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Load, MappedColumn, Session, joinedload, load_only, raiseload
from sqlalchemy.orm.attributes import flag_modified

from .filter import DatabaseFilter
from .model import Model
from .session import SessionFactory
from .sort import DatabaseSorter
from ..core import DataSourceError, ReqFieldsTree


SubPath = tuple[str | None, ReqFieldsTree]


class Database(ABC):
    """Encapsulates basic operations on a Database"""

    @abstractmethod
    def get_by_id(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        requested_tree: ReqFieldsTree | None = None,
    ) -> Model | None:
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
        filters: DatabaseFilter | None = None,
        sort_by: DatabaseSorter | None = None,
        offset: int | None = None,
        limit: int | None = None,
        requested_tree: ReqFieldsTree | None = None,
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
        filters: DatabaseFilter | None = None
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
        user_id: str | None = None
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
        user_id: str | None = None
    ) -> Model:
        """Performs an "upsert" on the given `Model` instance."""

    @abstractmethod
    def insert(
        self,
        instance: Model,
        in_session: Session,
        user_id: str | None = None
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
    ) -> Model | None:
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
    def attribute_types_including_id(self) -> dict[str, dict[str, type]]:
        """
        The mapping of attribute name to type for each model under
        this `Database` instance, including the ID attribute.
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
        models: list[type[Model]]
    ) -> None:

        self.__session_factory = session_factory
        self.__tablename_model_dict = self.__get_tablename_model_dict(models)
        self.__attribute_types_including_id = self.__get_attribute_types_including_id()
        self.__attribute_types = self.__get_attribute_types()

    @property
    def session_factory(self) -> SessionFactory:
        return self.__session_factory

    def get_by_id(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        requested_tree: ReqFieldsTree | None = None,
    ) -> Model | None:
        result = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session,
            requested_tree,
        )
        return result

    def get_page(
        self,
        tablename: str,
        in_session: Session,
        filters: DatabaseFilter | None = None,
        sort_by: DatabaseSorter | None = None,
        offset: int | None = None,
        limit: int | None = None,
        requested_tree: ReqFieldsTree | None = None,
    ) -> Iterable[Model]:

        model_dict = self.__tablename_model_dict
        model, query = self.__get_model_query(
            tablename,
            requested_tree=requested_tree,
        )

        filter_query = None
        if filters:
            # Dependency on the order in which methods on the DatabaseSorter
            # and DatabaseFilter objects are called could be cleaned up.
            if sort_by is not None:
                filters.add_field(sort_by.term)
            filter_query = self.__get_filter_query(tablename, filters)
            if sort_by is not None:
                filter_query = sort_by.sort(filter_query, tablename, model_dict, filters)

        if sort_by is None:
            query = query.order_by(model.get_id_column())
        else:
            query = sort_by.sort(query, tablename, model_dict)

        if limit is not None and offset is not None:
            if filters:
                filter_query = filter_query.limit(limit).offset(offset)
            else:
                query = query.limit(limit).offset(offset)

        if filters:
            # Add the filter query as a common table expression
            filter_cte = filter_query.cte()
            query = query.join(
                filter_cte,
                getattr(filter_cte.c, model.get_id_column_name()) == model.get_id_column(),
            )
        return in_session.scalars(query).unique().all()

    def count(
        self,
        tablename: str,
        in_session: Session,
        filters: DatabaseFilter | None = None,
    ) -> int:

        model = self.__tablename_model_dict[tablename]
        query = (
            self.__get_filter_query(tablename, filters=filters)
            if filters
            else select(model.get_id_column())
        )
        (n,) = in_session.execute(select(func.count()).select_from(query.subquery())).one()
        return n

    def delete(
        self,
        tablename: str,
        instance_id: Any,
        in_session: Session,
        user_id: str | None = None
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
        user_id: str | None = None,
        merge_collections: bool | None = None,
    ) -> Model:

        instance = self.__upsert_to_session(
            instance,
            in_session,
            merge_collections,
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
        user_id: str | None = None,
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
    ) -> Model | None:

        instance = self.__get_instance_by_id(
            tablename,
            instance_id,
            in_session
        )
        # It's possible for the relationship to be None when the foreign key is set but the
        # related object doesn't exist, so we check for the existence of the instance first before
        # trying to access the relationship
        if instance:
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

    def get_stats(
        self,
        tablename: str,
        stats_fields: list[str],
        stats: list[str],
        in_session: Session,
    ) -> dict[str, dict[str, dict[str, int]]]:
        all_stats = self.__all_table_stats(in_session)
        tbl_ret_stats = {}

        if tbl_stats := all_stats.get(tablename):
            for col in stats_fields:
                if col_stats := tbl_stats.get(col):
                    col_ret_stats = tbl_ret_stats.setdefault(col, {})
                    for stat_name in stats:
                        col_ret_stats[stat_name] = col_stats.get(stat_name)
        return {'stats': tbl_ret_stats}

    @ttl_cache(ttl=60)
    def __all_table_stats(self, in_session: Session):
        """Cached for a short time so that the query isn't rerun for each table"""
        tbl_model = self.__tablename_model_dict

        stats = in_session.execute(text("""
            SELECT
              s.tablename,
              s.attname AS column,
              CASE
                WHEN s.n_distinct < 0 THEN
                  CAST (-1 * s.n_distinct * t.n_live_tup AS INT)
                ELSE CAST (s.n_distinct AS INT)
              END AS cardinality
            FROM
              pg_stats AS s
              JOIN pg_stat_user_tables AS t
                ON s.tablename = t.relname
                AND s.schemaname = t.schemaname
            WHERE
              s.schemaname = current_schema
        """)).fetchall()

        tbl_stats = {}
        for tbl, col, card_n in stats:
            if col == tbl_model[tbl].get_id_column_name():
                col = 'id'
            tbl_stats.setdefault(tbl, {})[col] = {'cardinality': card_n}
        return tbl_stats

    def get_group_stats(
        self,
        tablename: str,
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
        in_session: Session,
        filters: DatabaseFilter | None = None,
    ) -> list[dict[str, dict[str, Any]]]:

        model = self.__tablename_model_dict[tablename]
        query = select().select_from(model)
        filter_query = self.__get_filter_query(tablename, filters=filters) if filters else None

        query = self.__apply_group_by(
            query,
            model,
            group_by,
            filters,
        )
        query = self.__apply_stats(
            query,
            filters,
            model,
            stats_fields,
            stats,
        )

        if filters:
            filter_cte = filter_query.cte()
            query = query.join(
                filter_cte,
                getattr(filter_cte.c, model.get_id_column_name()) == model.get_id_column(),
            )

        return self.__get_stats_from_query(
            in_session,
            query,
            group_by,
            stats_fields,
            stats,
        )

    @property
    def attribute_types(self) -> dict[str, dict[str, type]]:
        return self.__attribute_types

    @property
    def attribute_types_including_id(self) -> dict[str, dict[str, type]]:
        return self.__attribute_types_including_id

    def __get_stats_from_query(
        self,
        in_session: Session,
        query: Select,
        group_by: list[str],
        stats_fields: list[str],
        stats: list[str],
    ) -> list[dict[str, dict[str, Any]]]:

        results = in_session.execute(query).all()

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

        stats_dict = self.__parse_stats_dict(
            result,
            group_by,
            stats_fields,
            stats,
        )
        group_keys = self.__parse_group_keys(
            result,
            group_by,
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
        query: Select,
        filters: DatabaseFilter | None,
        model: type[Model],
        stats_fields: list[str],
        stats: list[str],
    ) -> Select:

        stat_columns = []

        for field in stats_fields:
            column = self.__get_column(
                filters,
                field,
            )
            stat_columns.extend(
                self.__apply_stats_for_field(
                    column,
                    stats,
                )
            )

        stat_columns.append(func.count())

        return query.add_columns(*stat_columns)

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
        filters: DatabaseFilter,
        field: str
    ) -> MappedColumn:

        column = filters.get_column(field)
        if '.' in field:
            filters.add_field(field)

        return column

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
        query: Select,
        model: type[Model],
        group_by: list[str],
        filters: DatabaseFilter,
    ) -> Select:
        """Must be done last in `get_group_stats()`."""

        g_columns = []

        for g in group_by:
            g_column = self.__get_column(
                filters,
                g
            )
            g_columns.append(g_column)

        return query.group_by(*g_columns).order_by(*g_columns).add_columns(*g_columns)

    def __get_attribute_types(self) -> dict[str, dict[str, type]]:
        return {
            t: {
                k: v for k, v in self.__attribute_types_including_id[t].items()
                if k != 'id'  # Exclude ID attribute
            }
            for t in self.__attribute_types_including_id.keys()
        }

    def __get_attribute_types_including_id(self) -> dict[str, dict[str, type]]:
        return {
            t: m.get_attribute_types() | {'id': m.get_id_attribute_type()}
            for t, m in self.__tablename_model_dict.items()
        }

    def __get_filter_query(
        self,
        tablename: str,
        filters: DatabaseFilter,
    ):
        model = self.__tablename_model_dict[tablename]
        query = filters.get_query(model)
        return filters.filter(query)

    def __get_model_query(
        self,
        tablename: str,
        requested_tree: ReqFieldsTree | None = None,
    ) -> tuple[type[Model], Select]:

        model = self.__tablename_model_dict[tablename]
        query = select(model).select_from(model)
        if requested_tree:
            query = self.add_options_to_query(query, tablename, requested_tree)

        return model, query

    def __commit_session(
        self,
        in_session: Session,
        instance: Model,
        operation: str,
        user_id: str | None = None,
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
        user_id: str | None,
    ) -> None:

        instance.before_commit(user_id=user_id)
        in_session.merge(instance)

    def __get_instance_by_id(
        self,
        tablename: str,
        instance_id: str,
        in_session: Session,
        requested_tree: ReqFieldsTree | None = None,
    ) -> Model | None:
        """
        Gets an instance by its tablename and id.
        """

        model, query = self.__get_model_query(
            tablename,
            requested_tree=requested_tree,
        )
        result = in_session.scalars(
            query.filter(model.get_id_column() == instance_id)
        ).one_or_none()
        return result

    def __get_tablename_model_dict(
        self,
        models: list[type[Model]]
    ) -> dict[str, type[Model]]:

        return {
            m.get_table_name(): m for m in models
        }

    def __upsert_to_session(
        self,
        instance: Model,
        in_session: Session,
        merge_collections: bool | None,
    ) -> Model:

        old_instance = self.__get_instance_by_id(
            instance.get_table_name(),
            instance.instance_id,
            in_session
        )
        if old_instance is not None:
            instance = self.__handle_difference(
                old_instance,
                instance,
                merge_collections,
            )
            in_session.flush()
            return instance

        in_session.add(instance)
        return instance

    def __handle_difference(
        self,
        old: Model,
        new: Model,
        merge_collections: bool | None,
    ) -> Model:
        """
        Performs various pre-merge operations, including:

        - merging `list`s and `dict`s like `ElasticDataSource`.
        """

        if merge_collections is not False:
            self.__handle_diff_dict(old, new)
            self.__handle_diff_list(old, new)

        __keys = [
            *new.get_attribute_types(),
            *new.get_all_foreign_key_names(),
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
            k for k in instance.get_attribute_types().keys()  # noqa: SIM118
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

    def add_options_to_query(
        self,
        query: Select,
        tablename: str,
        requested_tree: ReqFieldsTree,
    ):
        options = self.joinedload_options(requested_tree)
        # `raiseload(*)` acts as a trap, raising an exception if any methods
        # on the returned objects are called which would trigger loading data
        # from the database via another SELECT.
        if options:
            for load in options:
                query = query.options(load)
            query = query.options(raiseload('*'))
        return query

    def joinedload_options(self, tree: ReqFieldsTree) -> list[Load]:
        """
        Returns a list of SQLAlchemy `Load` objects based on the supplied
        `ReqFieldsTree` which specify which related tables to join into and
        which attribute columns to select.  This list of `Load` objects can
        then be added to a SQLAlchemy `Select` via `options()`.
        """
        sub: SubPath = None, tree
        return list(self.__joinedload_iter(sub))

    def __joinedload_iter(self, sub: SubPath, *path: list[SubPath]):
        path = [*path, sub]
        tree = sub[1]
        if tree.is_leaf:
            if options := self.__joinedload_options_from_path(path):
                yield options
        else:
            for sub in tree.sub_trees():
                yield from self.__joinedload_iter(sub, *path)

    def __joinedload_options_from_path(self, path: list[SubPath]):
        load = None
        prev_model = None
        for rel_name, tree in path:
            model = self.__tablename_model_dict[tree.object_type]
            if prev_model:
                # Add a joinedload for this model if `tree` isn't the root
                relation = getattr(prev_model, rel_name)
                load = load.joinedload(relation) if load else joinedload(relation)
            if names := tree.attribute_names:
                # SQLAlchemy will always add the primary key to the query, but
                # if the `.id` column isn't the primary key then
                # serialization to JSON will fail with the `raiseload` trap.
                # Adding it unconditionally here is harmless - it won't
                # appear twice in the SELECT statement.
                names.append(model.get_id_column_name())

                for col_name in model.get_all_foreign_key_names():
                    # Always load any to-one ID columns where the relation
                    # isn't being fetched so that we can create stub objects
                    # for them.
                    if not tree.has_attribute(col_name):
                        names.append(col_name)
                cols = [getattr(model, x) for x in names if x != 'id']
                load = (
                    load.load_only(*cols, raiseload=True)
                    if load
                    else load_only(*cols, raiseload=True)
                )
            prev_model = model

        return load
