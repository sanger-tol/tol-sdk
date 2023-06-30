# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .converter import Converter
from .database import Database
from .filter import DatabaseFilter
from .model import Model
from .relationship import SqlRelationshipConfig
from .sort import DatabaseSorter
from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceFilter
)
from ..core.abc import DetailGetter, ListGetter, PageGetter
from ..core.factory import DataObjectFactory
from ..core.relationship import RelationshipConfig


ConverterFactory = Callable[[DataObjectFactory], Converter]
FilterFactory = Callable[[DataSourceFilter], DatabaseFilter]
SorterFactory = Callable[[Optional[str]], DatabaseSorter]


class SqlDataSource(DataSource, DetailGetter, ListGetter, PageGetter):
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
        filter_factory: FilterFactory,
        sorter_factory: SorterFactory
    ) -> None:

        self.__db = db
        self.__type_tablename_map = type_tablename_map
        self.__supported_types = list(type_tablename_map.keys())
        self.__relationship_config = relationship_config.to_dict()
        self.__converter_factory = converter_factory
        self.__filter_factory = filter_factory
        self.__sorter_factory = sorter_factory

    def get_attribute_types(self, object_type: str) -> Dict[str, str]:
        raise NotImplementedError()

    @property
    def supported_types(self) -> List[str]:
        return self.__supported_types

    @property
    def relationship_config(self) -> Optional[Dict[str, RelationshipConfig]]:
        return self.__relationship_config

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
    ) -> Iterable[Optional[DataObject]]:

        # TODO maybe optimise on DB, and get multiple at once?
        models = self.__get_model_list_by_ids(object_type, object_ids)
        converter = self.__converter_factory(self.data_object_factory)
        return converter.convert(models)

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None,
    ) -> Tuple[Iterable[DataObject], int]:

        tablename = self.__type_tablename_map[object_type]
        database_filter = self.__filter_factory(object_filters)
        sorter = self.__sorter_factory(sort_by)
        total_count = self.__db.count(tablename, filters=database_filter)
        models = self.__get_list_page_models(
            tablename,
            database_filter,
            page_number,
            page_size,
            sorter
        )
        converter = self.__converter_factory(self.data_object_factory)
        return converter.convert(models), total_count

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> Iterable[DataObject]:
        models = self.__generate_models_for_get_list(
            object_type,
            object_filters=object_filters,
            sort_by=sort_by
        )
        converter = self.__converter_factory(self.data_object_factory)
        return converter.convert(models)

    def __generate_models_for_get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> Iterable[Model]:
        page = 1
        tablename = self.__type_tablename_map[object_type]
        database_filter = self.__filter_factory(object_filters)
        database_sorter = self.__sorter_factory(sort_by)
        page_size = self.get_page_size()
        while True:
            models_iterable = self.__db.get_list(
                tablename,
                filters=database_filter,
                sort_by=database_sorter,
                offset=(page - 1) * page_size,
                limit=page_size
            )
            models = list(models_iterable)
            if len(models) == 0:
                return
            yield from models
            page += 1

    def __get_model_list_by_ids(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
    ) -> List[Optional[Model]]:

        return [
            self.__db.get_by_id(
                self.__type_tablename_map[object_type],
                id_
            )
            for id_ in object_ids
        ]

    def __get_list_page_models(
        self,
        tablename: str,
        filters: Optional[DatabaseFilter],
        page_number: Optional[int],
        page_size: Optional[int],
        sort_by: Optional[DatabaseSorter]
    ) -> Iterable[Model]:
        offset = self.__get_offset(page_number, page_size)
        return self.__db.get_list(
            tablename,
            filters=filters,
            sort_by=sort_by,
            offset=offset,
            limit=page_size
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
