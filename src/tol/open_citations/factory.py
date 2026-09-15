# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import OpenCitationsApiClient
from .converter import OpenCitationsApiConverter
from .open_citations_datasource import (
    OpenCitationsConverterFactory,
    OpenCitationsDataSource,
)
from .parser import DefaultParser
from ..core import DataSource


class _OpenCitationsDSDict(Mapping):
    def __init__(self, api_ds: OpenCitationsDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> OpenCitationsDataSource:
        if __k not in self.__ds.supported_types:
            raise KeyError()
        return self.__ds

    def __iter__(self) -> Iterator[str]:
        return iter(self.__ds.supported_types)

    def __len__(self) -> int:
        return len(self.__ds.supported_types)


class _ConverterFactory:
    """
    Manages the instantiation of:

    - `OpenCitationsApiConverter`
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

    def open_citations_converter_factory(self) -> OpenCitationsConverterFactory:
        """
        Returns an instantiated `OpenCitationsApiConverter`.
        """
        parser = DefaultParser(self.__ds_dict)
        return OpenCitationsApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _OpenCitationsDSDict(self.data_source)


def _get_client_factory(
    open_citations_url: str,
    access_token: Optional[str] = None,
) -> Callable[[], OpenCitationsApiClient]:
    """
    A reasonable default for creating an `OpenCitationsApiClient` instance.
    """
    return lambda: OpenCitationsApiClient(
        open_citations_url,
        access_token,
    )


def create_open_citations_datasource(
    open_citations_url: str,
    access_token: Optional[str] = None,
) -> OpenCitationsDataSource:
    """
    Instantiates `OpenCitationsDataSource` using the given:

    - `open_citations_url`
    - `access_token` (optional)
    """
    client_factory = _get_client_factory(
        open_citations_url,
        access_token,
    )
    manager = _ConverterFactory()

    open_citations_ds = OpenCitationsDataSource(
        client_factory,
        manager.open_citations_converter_factory,
    )

    manager.data_source = open_citations_ds

    return open_citations_ds
