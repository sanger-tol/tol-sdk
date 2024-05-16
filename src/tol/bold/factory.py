# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .bold_datasource import (
    BoldConverterFactory,
    BoldDataSource
)
from .client import BoldApiClient
from .converter import (
    BoldApiConverter
)
from .parser import DefaultParser
from ..core import DataSource


class _BoldDSDict(Mapping):
    def __init__(self, api_ds: BoldDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> BoldDataSource:
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

    - `BoldApiConverter`
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

    def bold_converter_factory(self) -> BoldConverterFactory:
        """
        Returns an instantiated `BoldApiConverter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return BoldApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _BoldDSDict(self.data_source)


def _get_client_factory(
    api_url: str,
    api_key: str
) -> Callable[[], BoldApiClient]:
    """
    A resonable default for creating
    a `BoldApiClient` instance
    """

    return lambda: BoldApiClient(
        api_url,
        api_key
    )


def create_bold_datasource(
    bold_url: str,
    bold_api_key: str
) -> BoldDataSource:
    """
    Instantiates `BoldDataSource` using the given:

    - `bold_url`
    - `bold_api_key`
    """

    client_factory = _get_client_factory(
        bold_url,
        bold_api_key
    )
    manager = _ConverterFactory()

    bold_ds = BoldDataSource(
        client_factory,
        manager.bold_converter_factory
    )

    manager.data_source = bold_ds

    return bold_ds
