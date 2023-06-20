# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, Iterable, List, Optional, Tuple

from .converter import Converter, DefaultConverter, TypeFunction
from .database import Database
from .filter import DatabaseFilter, DefaultDatabaseFilter
from .model import Model
from .sort import DatabaseSorter, DefaultDatabaseSorter
from ..core import DataId, DataObject, DataSource, DataSourceFilter, unsupported


ConverterFactory = Callable[[], Converter]


class SqlDataSource(DataSource):
    """
    A DataSource for manipulating DataObject instances as
    defined by Sqlalchemy models on a DB connection.
    """

    def __init__(
        self,
        db: Database,
        type_tablename_map: Dict[str, str],
        converter_factory: Optional[ConverterFactory] = None
    ) -> None:

        self.__db = db
        self.__type_tablename_map = type_tablename_map
        self.__supported_types = list(type_tablename_map.keys())
        self.__set_converter_factory(converter_factory)

    def get_attribute_types(self, object_type: str) -> Dict[str, str]:
        raise NotImplementedError()

    @property
    def supported_types(self) -> List[str]:
        return self.__supported_types

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
    ) -> Iterable[Optional[DataObject]]:

        # TODO maybe optimise on DB, and get multiple at once?
        models = self.__get_model_list_by_ids(object_type, object_ids)
        converter = self.__converter_factory()
        return converter.convert(models)

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
    ) -> Tuple[Iterable[DataObject], int]:

        tablename = self.__type_tablename_map[object_type]
        database_filter = DefaultDatabaseFilter(object_filters)
        sorter = DefaultDatabaseSorter(sort_by) if sort_by is not None else None
        total_count = self.__db.count(tablename, filters=database_filter)
        models = self.__get_list_page_models(
            tablename,
            database_filter,
            page_number,
            page_size,
            sorter
        )
        converter = self.__converter_factory()
        return converter.convert(models), total_count

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        sort_by: str = None
    ) -> Iterable[DataObject]:

        models = self.__db.get_list(
            self.__type_tablename_map[object_type],
            filters=object_filters,
            sort_by=sort_by
        )
        converter = self.__converter_factory()
        return converter.convert(models)

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

    def __set_converter_factory(
        self,
        converter_factory: Optional[ConverterFactory]
    ) -> None:

        if converter_factory is None:
            self.__converter_factory = self.__default_converter_factory()
        else:
            self.__converter_factory = converter_factory

    def __default_converter_factory(self) -> ConverterFactory:
        tablename_type_map = {
            v: k
            for k, v in self.__type_tablename_map.items()
        }
        type_function: TypeFunction = lambda c: tablename_type_map[
            c.get_table_name()
        ]
        return lambda: DefaultConverter(type_function)

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

    @unsupported
    def get_aggregations(self, *args, **kwargs):
        pass
