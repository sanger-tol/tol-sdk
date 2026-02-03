# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# from collections.abc import Iterable

from ..core import DataObject, DataSourceParser
from .parser import ElasticApiResource


class ElasticApiConverter:
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

    # def convert_list(self, input_: ElasticApiResource) -> Iterable[DataObject]:
    #     return (
    #         self.__parser.parse(obj)
    #         for obj in input_.values()
    #     )
