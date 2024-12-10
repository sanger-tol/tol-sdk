# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import CopoApiClient
from .converter import (
    CopoApiConverter
)
from .copo_datasource import (
    CopoConverterFactory,
    CopoDataSource
)
from .parser import DefaultParser
from ..core import DataSource


class _CopoDSDict(Mapping):
    def __init__(self, api_ds: CopoDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> CopoDataSource:
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

    - `CopoApiConverter`
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

    def copo_converter_factory(self) -> CopoConverterFactory:
        """
        Returns an instantiated `CopoApiConverter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return CopoApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _CopoDSDict(self.data_source)


def _get_client_factory(
    api_url: str
) -> Callable[[], CopoApiClient]:
    """
    A resonable default for creating
    a `JsonApiClient` instance
    """

    return lambda: CopoApiClient(
        api_url
    )


def create_copo_datasource(
    copo_url: str
) -> CopoDataSource:
    """
    Instantiates `CopoDataSource` using the given:

    - `copo_url`
    """

    client_factory = _get_client_factory(
        copo_url
    )
    manager = _ConverterFactory()

    copo_ds = CopoDataSource(
        client_factory,
        manager.copo_converter_factory
    )

    manager.data_source = copo_ds

    return copo_ds
