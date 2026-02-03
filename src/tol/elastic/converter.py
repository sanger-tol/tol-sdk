# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import DataSourceParser

from .parser import ElasticApiResource


class ElasticConverter:
    """
    Converts from Elastic API transfers to instances of `DataObject`
    """
    __slots__ = ['__parser']
    __parser: DataSourceParser[ElasticApiResource]

    def __init__(self, parser: DataSourceParser[ElasticApiResource]) -> None:
        self.__parser = parser
