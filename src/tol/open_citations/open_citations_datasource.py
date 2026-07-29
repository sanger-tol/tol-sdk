# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Callable, Iterable, Optional

from .client import OpenCitationsApiClient
from .converter import OpenCitationsApiConverter
from ..core import DataObject, DataSource, DataSourceError
from ..core.operator import DetailGetter

ClientFactory = Callable[[], OpenCitationsApiClient]
OpenCitationsConverterFactory = Callable[[], OpenCitationsApiConverter]


class OpenCitationsDataSource(
    DataSource,
    DetailGetter,
):
    """
    A `DataSource` that connects to a remote OpenCitations API.

    Developers should likely use `create_open_citations_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        open_citations_converter_factory: OpenCitationsConverterFactory,
    ) -> None:
        self.__client_factory = client_factory
        self.__converter_factory = open_citations_converter_factory
        super().__init__({})

    @property
    @cache
    def __client(self) -> OpenCitationsApiClient:
        return self.__client_factory()

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'meta': {
                'id': 'str',
                'title': 'str',
                'author': 'str',
                'pub_date': 'str',
                'venue': 'str',
                'volume': 'str',
                'issue': 'str',
                'page': 'str',
                'type': 'str',
                'publisher': 'str',
                'editor': 'str'
            },
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(self.attribute_types.keys())

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[DataObject]]:
        self.__validate_object_type(object_type)
        requested_object_ids = [str(object_id) for object_id in object_ids]

        open_citations_response = self.__client.get_detail(
            object_type,
            requested_object_ids,
        )
        open_citations_converter = self.__converter_factory()

        converted_objects, _ = open_citations_converter.convert_list(
            object_type,
            open_citations_response,
        ) if open_citations_response is not None else ([], 0)
        yield from self.sort_by_id(
            converted_objects,
            requested_object_ids,
        )

    def __validate_object_type(self, object_type: str) -> None:
        if object_type not in self.supported_types:
            raise DataSourceError(
                title='Unsupported object type',
                detail=(
                    f"Object type '{object_type}' is not supported by this datasource."
                ),
            )
