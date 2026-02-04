# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable

from .parser import ElasticApiResource
from ..core import Converter, DataObject, DataSourceParser


class ElasticApiConverter(Converter[ElasticApiResource, DataObject]):
    """
    Converts from Elastic API transfers to instances of `DataObject`
    """
    __slots__ = ['__parser']
    __parser: DataSourceParser[ElasticApiResource]

    def __init__(self, parser: DataSourceParser[ElasticApiResource]) -> None:
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
    # TODO
    pass
