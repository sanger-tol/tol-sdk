# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Callable, Iterable, Optional

from .client import OpenCitationsApiClient
from .converter import OpenCitationsApiConverter
from ..core import DataObject, DataSource, DataSourceError, DataSourceFilter
from ..core.operator import DetailGetter, ListGetter

ClientFactory = Callable[[], OpenCitationsApiClient]
OpenCitationsConverterFactory = Callable[[], OpenCitationsApiConverter]


class OpenCitationsDataSource(
    DataSource,
    DetailGetter,
    ListGetter,
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
                'pmid': 'str',
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
        objects_by_id = {
            f'doi:{data_object.id}'.lower(): data_object
            for data_object in converted_objects
        }
        for data_object in converted_objects:
            pmid = data_object.attributes.get('pmid')
            if pmid:
                objects_by_id[f'pmid:{pmid}'.lower()] = data_object

        for object_id in requested_object_ids:
            lookup_id = object_id if ':' in object_id else f'doi:{object_id}'
            yield objects_by_id.get(lookup_id.lower())

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        **kwargs,
    ) -> Iterable[DataObject]:
        self.__validate_object_type(object_type)
        object_ids = object_filters.and_['reference_id']['in_list']['value']
        open_citations_response = self.__client.get_detail(object_type, object_ids)
        converted_objects, _ = self.__converter_factory().convert_list(
            object_type,
            open_citations_response,
        ) if open_citations_response is not None else ([], 0)
        return iter(converted_objects)

    def __validate_object_type(self, object_type: str) -> None:
        if object_type not in self.supported_types:
            raise DataSourceError(
                title='Unsupported object type',
                detail=(
                    f"Object type '{object_type}' is not supported by this datasource."
                ),
            )
