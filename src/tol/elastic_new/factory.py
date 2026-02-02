# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import ElasticApiClient
from .converter import (
    ElasticApiConverter
)
from .filter import DefaultElasticFilter
from .elastic_datasource import (
    GoatConverterFactory,
    ElasticDataSource
)
from .parser import DefaultParser
from ..core import DataSource


class _GoatDSDict(Mapping):
    def __init__(self, api_ds: ElasticDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> ElasticDataSource:
        if __k not in self.__ds.supported_types:
            raise KeyError()
        return self.__ds

    def __iter__(self) -> Iterator[str]:
        return iter(self.__ds.supported_types)

    def __len__(self) -> int:
        return len(self.__ds.supported_types)


class _ConverterFactory:
    """
    Manges the instantation of:

    - `GoatApiConverter`
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

    def goat_converter_factory(self) -> GoatConverterFactory:
        """
        Returns an instantiated `GoatApiConverter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return ElasticApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _GoatDSDict(self.data_source)


class _FilterFactory:
    """
    Manges the instantation of:

    - `GoatFilter`
    """

    def __init__(self) -> None:
        pass

    def goat_filter_factory(self) -> DefaultElasticFilter:
        """
        Returns an instantiated `GoatFilter`.
        """

        return DefaultElasticFilter()


def _get_client_factory(
    api_url: str
) -> Callable[[], ElasticApiClient]:
    """
    A resonable default for creating
    a `GoatApiClient` instance
    """

    return lambda: ElasticApiClient(
        api_url
    )


def create_goat_datasource(
    goat_url: str
) -> ElasticDataSource:
    """
    Instantiates `GoatDataSource` using the given:

    - `goat_url`
    """

    client_factory = _get_client_factory(
        goat_url
    )
    manager = _ConverterFactory()
    filter_factory = _FilterFactory()
    goat_ds = ElasticDataSource(
        client_factory,
        manager.goat_converter_factory,
        filter_factory.goat_filter_factory
    )

    manager.data_source = goat_ds

    return goat_ds
