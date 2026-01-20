# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import DummyClient
from .converter import (
    DummyConverter
)
from .dummy_datasource import (
    DummyConverterFactory,
    DummyDataSource
)
from .parser import DefaultParser
from ..core import DataSource


class _DummyDSDict(Mapping):
    def __init__(self, api_ds: DummyDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> DummyDataSource:
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

    - `DummyConverter`
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

    def dummy_converter_factory(self) -> DummyConverterFactory:
        """
        Returns an instantiated `DummyConverter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return DummyConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _DummyDSDict(self.data_source)


def _get_client_factory() -> Callable[[], DummyClient]:
    """
    A resonable default for creating
    a `DummyClient` instance
    """

    return lambda: DummyClient()


def create_dummy_datasource() -> DummyDataSource:
    """
    Instantiates `DummyDataSource`
    """

    client_factory = _get_client_factory()
    manager = _ConverterFactory()

    dummy_ds = DummyDataSource(
        client_factory,
        manager.dummy_converter_factory
    )

    manager.data_source = dummy_ds

    return dummy_ds
