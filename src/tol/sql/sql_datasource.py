# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session as SqlaSession

from .database import Database
from .ds_session import SqlDataSourceSession
from .filter import DatabaseFilter
from .model import Model
from .relationship import SqlRelationshipConfig
from .sort import DatabaseSorter
from .sql_converter import DataObjectConverter, ModelConverter
from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceFilter,
    UserIdGetter
)
from ..core.factory import DataObjectFactory
from ..core.operator import (
    Counter,
    Cursor,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    RelationWriteMode,
    Relational,
    ReturnMode,
    Upserter,
)
from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


ConverterFactory = Callable[
    [DataObjectFactory, list[str] | None],
    ModelConverter
]
BackConverterFactory = Callable[[], DataObjectConverter]
FilterFactory = Callable[[DataSourceFilter], DatabaseFilter]
SorterFactory = Callable[[Optional[str]], DatabaseSorter]


class SqlDataSource(
    Counter,
    Cursor,
    DataSource,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Relational,
    Upserter
):
    """
    A DataSource for manipulating DataObject instances as
    defined by Sqlalchemy models on a DB connection.
    """

    def __init__(
        self,
        db: Database,
        type_tablename_map: Dict[str, str],
        relationship_config: SqlRelationshipConfig,
        converter_factory: ConverterFactory,
        back_converter_factory: BackConverterFactory,
        filter_factory: FilterFactory,
        sorter_factory: SorterFactory,
        user_id_getter: Optional[UserIdGetter] = None
    ) -> None:

        self.__db = db
        self.__type_tablename_map = type_tablename_map
        self.__supported_types = list(type_tablename_map.keys())
        self.__relationship_config = relationship_config.to_dict()
        self.__converter_factory = converter_factory
        self.__back_converter_factory = back_converter_factory
        self.__filter_factory = filter_factory
        self.__sorter_factory = sorter_factory
        self.__all_attribute_types = self.__calculate_all_attribute_types()
        self.__set_user_id_getter(user_id_getter)
        self.write_batch_size = 100

        super().__init__({})

    def create_sqla_session(self) -> SqlaSession:
        return self.__db.session_factory()

    def get_session(self) -> OperableSession:
        return SqlDataSourceSession(self)

    @property
    def _default_write_mode(self) -> RelationWriteMode:
        return RelationWriteMode.SEPARATE

    @property
    def _default_return_mode(self) -> ReturnMode:
        return ReturnMode.POPULATED

    def __get_sqla_session(
        self,
        session: Optional[SqlDataSourceSession]
    ) -> SqlaSession:

        return (
            session._sqla_session
            if session is not None
            else self.create_sqla_session()
        )

    @property
    def attribute_types(self) -> Dict[str, str]:
        return self.__all_attribute_types

    @property
    def supported_types(self) -> List[str]:
        return self.__supported_types

    @property
    def relationship_config(self) -> Optional[Dict[str, RelationshipConfig]]:
        return self.__relationship_config

    def get_count(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[SqlDataSourceSession] = None
    ) -> int:
        """
        Counts the number of results that are matched by the (optional) filter
        """

        tablename = self.__type_tablename_map[object_type]
        database_filter = self.__filter_factory(
            self._preprocess_filter(object_type, object_filters)
        )
        in_session = self.__get_sqla_session(session)
        total_count = self.__db.count(
            tablename,
            in_session,
            filters=database_filter
        )
        if session is None:
            in_session.close()
        return total_count

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        session: Optional[SqlDataSourceSession] = None,
        requested_fields: list[str] | None = None,
    ) -> Iterable[Optional[DataObject]]:

        in_session = self.__get_sqla_session(session)
        models = self.__get_model_list_by_ids(
            object_type,
            object_ids,
            in_session,
            requested_fields,
        )
        converter = self.__get_converter()
        return_list = list(
            converter.convert_iterable(models)
        )
        if session is None:
            in_session.close()
        return return_list

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None,
        session: Optional[SqlDataSourceSession] = None,
        requested_fields: list[str] | None = None
    ) -> Tuple[Iterable[DataObject], int]:

        tablename = self.__type_tablename_map[object_type]
        database_filter = self.__filter_factory(
            self._preprocess_filter(object_type, object_filters)
        )
        sorter = self.__sorter_factory(sort_by)
        in_session = self.__get_sqla_session(session)
        total_count = self.__db.count(
            tablename,
            in_session,
            filters=database_filter
        )
        models = self.__get_list_page_models(
            tablename,
            database_filter,
            page_number,
            page_size,
            sorter,
            in_session,
            requested_relationships=self.__format_requested_relationships(
                object_type,
                requested_fields
            ),
        )
        converter = self.__get_converter(
            requested_fields=requested_fields
        )
        return_list = list(
            converter.convert_iterable(models)
        )
        if session is None:
            in_session.close()
        return return_list, total_count

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[SqlDataSourceSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:

        if self.can_use_cursor(object_type, object_filters):
            return self._get_list_by_cursor(
                object_type,
                object_filters=self._preprocess_filter(object_type, object_filters),
                session=session,
                requested_fields=requested_fields
            )
        else:
            return self.__get_list_limit_offset(
                object_type,
                object_filters=object_filters,
                session=session,
                requested_fields=requested_fields,
            )

    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[SqlDataSourceSession] = None
    ) -> None:

        tablename = self.__type_tablename_map[object_type]
        user_id = self.__user_id_getter()
        in_session = self.__get_sqla_session(session)
        for object_id in object_ids:
            self.__db.delete(
                tablename,
                object_id,
                in_session,
                user_id=user_id
            )
        if session is None:
            in_session.close()

    def get_cursor_page(
        self,
        object_type: str,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        search_after: list[str] | None = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> tuple[Iterable[DataObject], list[str] | None]:

        fetched, _ = self.get_list_page(
            object_type,
            1,
            page_size=page_size,
            object_filters=self.update_cursor_filters(
                search_after,
                object_filters
            ),
            sort_by='id',
            session=session,
            requested_fields=requested_fields,
        )

        return self.__format_cursor_page(fetched)

    def upsert_batch(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[SqlDataSourceSession] = None,
        **kwargs
    ) -> list[DataObject]:
        back_converter = self.__back_converter_factory()
        model_instances = back_converter.convert_iterable(objects)
        user_id = self.__user_id_getter()
        in_session = self.__get_sqla_session(session)
        returned_models = [
            self.__db.upsert(
                instance,
                in_session,
                user_id=user_id
            )
            for instance in model_instances
        ]
        return_list = list(
            self.__get_converter().convert_iterable(
                returned_models
            )
        )
        if session is None:
            in_session.close()
        return return_list

    def insert_batch(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[SqlDataSourceSession] = None
    ) -> Iterable[DataObject]:

        back_converter = self.__back_converter_factory()
        model_instances = back_converter.convert_iterable(objects)
        user_id = self.__user_id_getter()
        in_session = self.__get_sqla_session(session)
        inserted_list = [
            self.__db.insert(
                instance,
                in_session,
                user_id=user_id
            )
            for instance in model_instances
        ]
        return_list = list(
            self.__get_converter().convert_iterable(
                inserted_list
            )
        )
        if session is None:
            in_session.close()
        return return_list

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[SqlDataSourceSession] = None
    ) -> Optional[DataObject]:

        tablename = self.__type_tablename_map[source.type]
        in_session = self.__get_sqla_session(session)
        model = self.__db.get_to_one_relation(
            tablename,
            source.id,
            relationship_name,
            in_session,
        )
        return_ = self.__get_converter().convert_optional(model)
        if session is None:
            in_session.close()
        return return_

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[SqlDataSourceSession] = None
    ) -> Iterable[DataObject]:

        tablename = self.__type_tablename_map[source.type]
        in_session = self.__get_sqla_session(session)
        models = self.__db.get_to_many_relations(
            tablename,
            source.id,
            relationship_name,
            in_session
        )
        return_list = list(
            self.__get_converter().convert_iterable(models)
        )
        if session is None:
            in_session.close()
        return return_list

    def get_group_stats(
        self,
        object_type: str,
        group_by: list[str],
        stats_fields: list[str] = [],
        stats: list[str] = ['min', 'max'],
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> Iterable[dict[Any, int]]:

        tablename = self.__type_tablename_map[object_type]
        in_session = self.__get_sqla_session(session)
        filters = self.__filter_factory(
            self._preprocess_filter(object_type, object_filters)
        )

        return self.__db.get_group_stats(
            tablename,
            group_by,
            stats_fields,
            stats,
            in_session,
            filters=filters,
        )

    def __format_cursor_page(
        self,
        data_objects: Iterable[DataObject],
    ) -> tuple[Iterable[DataObject], list[str] | None]:

        return_list = list(data_objects)
        if return_list:
            return (
                return_list,
                [return_list[-1].id]
            )
        else:
            return [], None

    def __calculate_all_attribute_types(self) -> dict[str, dict[str, str]]:
        tablename_type_map = {
            v: k for k, v in self.__type_tablename_map.items()
        }

        return {
            tablename_type_map[k]: self.__calculate_attribute_types(v)
            for k, v in self.__db.attribute_types.items()
        }

    def __calculate_attribute_types(
        self,
        types: dict[str, type]
    ) -> dict[str, str]:

        return {
            k: v.__name__
            for k, v in types.items()
        }

    def __get_converter(
        self,
        requested_fields: list[str] | None = None,
    ) -> ModelConverter:

        return self.__converter_factory(
            self.data_object_factory,
            requested_fields,
        )

    def __get_list_limit_offset(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[SqlDataSourceSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:

        page_number = 1

        while True:
            (results, _) = self.get_list_page(
                object_type,
                page_number,
                object_filters=object_filters,
                session=session,
                requested_fields=requested_fields,
            )
            results = list(results)

            yield from results

            if len(results) < self.get_page_size():
                return

            page_number += 1

    def __get_model_list_by_ids(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        session: SqlaSession,
        requested_fields: list[str] | None,
    ) -> List[Optional[Model]]:

        requested_relationships = self.__format_requested_relationships(
            object_type,
            requested_fields,
        )

        return [
            self.__db.get_by_id(
                self.__type_tablename_map[object_type],
                id_,
                session,
                requested_relationships
            )
            for id_ in object_ids
        ]

    def __get_list_page_models(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter],
        page_number: Optional[int],
        page_size: Optional[int],
        sort_by: Optional[DatabaseSorter],
        in_session: SqlaSession,
        requested_relationships: dict[str, str] | None = None,
    ) -> Iterable[Model]:

        offset = self.__get_offset(page_number, page_size)
        return self.__db.get_page(
            tablename,
            in_session,
            filters=filters,
            sort_by=sort_by,
            offset=offset,
            limit=page_size,
            requested_relationships=requested_relationships,
        )

    def __get_offset(
        self,
        page_number: Optional[int],
        page_size: Optional[int]
    ) -> Optional[int]:

        return (
            None if page_number is None or page_size is None
            else (page_number - 1) * page_size
        )

    def __set_user_id_getter(
        self,
        user_id_getter: UserIdGetter
    ) -> None:

        self.__user_id_getter = (
            (lambda: None) if user_id_getter is None else user_id_getter
        )

    def __format_requested_relationships(
        self,
        object_type: str,
        requested_relationships: list[str] | None
    ) -> dict | None:

        if requested_relationships is None:
            return None

        rel_dict = {
            '__tablename__': self.__type_tablename_map[object_type]
        }

        for requested in requested_relationships:
            current_type = object_type
            # cut off the column
            relationships = requested.split('.')[:-1]
            current_dict = rel_dict

            for r in relationships:
                r_type = self.relationship_config[current_type].to_one[r]
                r_tablename = self.__type_tablename_map[r_type]

                if r not in current_dict:
                    current_dict[r] = {
                        '__tablename__': r_tablename
                    }

                current_dict = current_dict[r]
                current_type = r_type

        return rel_dict
