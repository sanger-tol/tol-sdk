# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, Optional

from .client import DummyClient
from .converter import (
    DummyConverter
)
from ..core import DataObject, DataSource, DataSourceError, DataSourceFilter
from ..core.operator import (
    DetailGetter,
    ListGetter
)

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession

ClientFactory = Callable[[], DummyClient]
DummyConverterFactory = Callable[[], DummyConverter]


class DummyDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter
):
    """
    A `DataSource` that outputs dummy data.

    Developers should likely use `create_dummy_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        dummy_converter_factory: DummyConverterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__dummy_converter_factory = dummy_converter_factory
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'record': {
                'big_string': 'str',
                'little_string': 'str',
                'bool': 'bool',
                'date': 'datetime',
                'int': 'int',
                'list': 'list[str]',
                'dict': 'dict[str,str]',
                'link': 'str',
                'links': 'list[str]',
                'image': 'dict[str,str]',
                'images': 'list[dict[str,str]]',
            },
            'category': {
                'name': 'str'
            },
            'sub_category': {
                'name': 'str',
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        client = self.__client_factory()
        dummy_response = client.get_detail(object_type, object_ids)
        dummy_converter = self.__dummy_converter_factory()

        converted_objects, _ = dummy_converter.convert_list(dummy_response) \
            if dummy_response is not None else ([], 0)
        yield from self.sort_by_id(converted_objects, object_ids)

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None,
        **kwargs
    ) -> Iterable[DataObject]:
        if object_filters:
            raise DataSourceError('Filtering is not supported')
        objects = self.__client_factory().get_list(
            object_type
        )
        converted_objects, _ = self.__dummy_converter_factory().convert_list(objects)
        return iter(converted_objects)
