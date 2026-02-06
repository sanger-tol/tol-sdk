# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable, Iterable

from .parser import ElasticApiResource
from ..core import Converter, DataObject, DataSourceParser
from ..core.operator.updater import DataObjectUpdate


class ElasticApiConverter(Converter[ElasticApiResource, DataObject]):
    """
    Converts from Elastic API transfers to instances of `DataObject`
    """
    __slots__ = ['__parser']
    __parser: DataSourceParser[ElasticApiResource, DataObject]

    def __init__(self, parser: DataSourceParser[ElasticApiResource, DataObject]) -> None:
        self.__parser = parser

    def convert(self, input_: ElasticApiResource) -> DataObject:
        """
        Converts an `ElasticApiTransfer` containing a detail (single) result
        """
        return self.__parser.parse(input_)

    def convert_list(
        self, input_: Iterable[ElasticApiResource]
    ) -> Iterable[DataObject]:
        """
        Converts a list of `ElasticApiTransfer`s to a list of `DataObjects`. Also returns
        a count of the total results meeting.
        """
        for elastic_resource in input_:
            yield self.__parser.parse(elastic_resource)


class DataObjectConverter(Converter[DataObject, ElasticApiResource]):
    __slots__ = ['__parser']
    __parser: DataSourceParser[DataObject, ElasticApiResource]

    def __init__(self, parser: DataSourceParser[DataObject, ElasticApiResource]) -> None:
        self.__parser = parser

    def convert(
        self,
        index: str,
        objects: Iterable[DataObject],
        id_func: Callable,
        field_prefix: str,
    ) -> ElasticApiResource:
        return self.__parser.parse(
            index,
            objects,
            id_func,
            field_prefix
        )


class DataObjectUpdateConverter(Converter[DataObjectUpdate, ElasticApiResource]):
    __slots__ = ['__parser']
    __parser: DataSourceParser[DataObjectUpdate, ElasticApiResource]

    def __init__(self, parser: DataSourceParser[DataObjectUpdate, ElasticApiResource]) -> None:
        self.__parser = parser

    def convert(
        self,
        object_type: str,
        update: dict,
        field_prefix: str,
        candidate_key: Iterable[str],
    ) -> ElasticApiResource:
        return self.__parser.parse(
            object_type,
            update,
            field_prefix,
            candidate_key,
        )
