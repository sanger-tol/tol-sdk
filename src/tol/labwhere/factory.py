# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import LabwhereApiClient
from .converter import (
    LabwhereApiConverter
)
from .labwhere_datasource import (
    LabwhereConverterFactory,
    LabwhereDataSource
)
from .parser import DefaultParser
from ..core import DataSource


class _LabwhereDSDict(Mapping):
    def __init__(self, api_ds: LabwhereDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> LabwhereDataSource:
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

    - `LabwhereApiConverter`
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

    def labwhere_converter_factory(self) -> LabwhereConverterFactory:
        """
        Returns an instantiated `LabwhereApiConverter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return LabwhereApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _LabwhereDSDict(self.data_source)


def _get_client_factory(
    api_url: str
) -> Callable[[], LabwhereApiClient]:
    """
    A resonable default for creating
    a `JsonApiClient` instance
    """

    return lambda: LabwhereApiClient(
        api_url
    )


def create_labwhere_datasource(
    labwhere_url: str
) -> LabwhereDataSource:
    """
    Instantiates `LabwhereDataSource` using the given:

    - `labwhere_url`
    """

    client_factory = _get_client_factory(
        labwhere_url
    )
    manager = _ConverterFactory()

    labwhere_ds = LabwhereDataSource(
        client_factory,
        manager.labwhere_converter_factory
    )

    manager.data_source = labwhere_ds

    return labwhere_ds
