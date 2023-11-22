# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Optional

from .api_datasource import (
    ApiDataSource,
    DOConverterFactory,
    JsonConverterFactory
)
from .client import JsonApiClient
from .converter import (
    DataObjectConverter,
    JsonApiConverter
)
from .filter import DefaultApiFilter
from ..core import DataSource


class _ConverterFactory:
    """
    Manges the instantation of:

    - `DataObjectConverter`
    - `JsonApiConverter`
    """

    def __init__(self) -> None:
        self.__data_source: Optional[DataSource] = None

    @property
    def data_source(self) -> Optional[DataSource]:
        return self.__data_source

    @data_source.setter
    def data_source(
        self,
        ds: DataSource
    ) -> None:

        self.__data_source = ds

    def do_converter_factory(self) -> DOConverterFactory:
        """
        Returns an instantiated `DataObjectConverter`.
        """

        return DataObjectConverter()

    def json_converter_factory(self) -> JsonConverterFactory:
        """
        Returns an instantiated `JsonApiConverter`.
        """

        do_factory = self.__data_source.data_object_factory
        return JsonApiConverter(do_factory)


def _get_client_factory(
    api_url: str,
    token: Optional[str]
) -> Callable[[], JsonApiClient]:
    """
    A resonable default for creating
    a `JsonApiClient` instance
    """

    return lambda: JsonApiClient(api_url, token=token)


def _filter_factory() -> DefaultApiFilter:
    return DefaultApiFilter()


def create_api_datasource(
    api_url: str,
    token: Optional[str] = None
) -> ApiDataSource:
    """
    Instantiates `ApiDataSource` using the given:

    - `api_url`
    - `token` (optional)
    """

    client_factory = _get_client_factory(
        api_url,
        token=token
    )
    manager = _ConverterFactory()

    api_ds = ApiDataSource(
        client_factory,
        manager.json_converter_factory,
        manager.do_converter_factory,
        _filter_factory
    )

    manager.data_source = api_ds

    return api_ds
