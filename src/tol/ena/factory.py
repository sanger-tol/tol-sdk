# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Dict, Iterator, Optional

from .client import EnaApiClient
from .converter import (
    EnaApiConverter
)
from .ena_datasource import (
    EnaConverterFactory,
    EnaDataSource
)
from .filter import DefaultEnaFilter
from .parser import DefaultParser
from ..core import DataSource


class _EnaDSDict(Mapping):
    def __init__(self, api_ds: EnaDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> EnaDataSource:
        if __k not in self.__ds.supported_types:
            raise KeyError()
        return self.__ds

    def __iter__(self) -> Iterator[str]:
        return iter(self.__ds.supported_types)

    def __len__(self) -> int:
        return len(self.__ds.supported_types)


class _ConverterFactory:
    """
    Manages the instantiation of

    - `EnaApiConverter`
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

    def ena_converter_factory(self) -> EnaConverterFactory:
        """
        Returns an instantiated `EnaApiConverter`.
        """
        parser = DefaultParser(self.__ds_dict)
        return EnaApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _EnaDSDict(self.data_source)


def _get_client_factory(
    ena_url: str,
    ena_user: str,
    ena_password: str,
    ena_contact_name: str,
    ena_contact_email: str
) -> Callable[[], EnaApiClient]:
    """
    A resonable default for creating an `EnaApiClient` instance.
    """
    return lambda: EnaApiClient(
        ena_url,
        ena_user,
        ena_password,
        ena_contact_name,
        ena_contact_email
    )


class _FilterFactory:
    """
    Manages the instantiation of

    - `EnaFilter`
    """

    def __init__(self) -> None:
        pass

    def ena_filter_factory(self) -> DefaultEnaFilter:
        """
        Returns an instantiated `EnaFilter`.
        """

        return DefaultEnaFilter()


def create_ena_datasource(
    ena_url: str,
    ena_user: str,
    ena_password: str,
    ena_contact_name: str,
    ena_contact_email: str
) -> EnaDataSource:
    """
    Instantiates `EnaDataSource` using the given:

    - `ena_url`
    - `ena_user`
    - `ena_password`
    - `ena_contact_name`
    - `ena_contact_email`
    """

    client_factory = _get_client_factory(
        ena_url,
        ena_user,
        ena_password,
        ena_contact_name,
        ena_contact_email
    )
    manager = _ConverterFactory()
    filter_factory = _FilterFactory()

    ena_ds = EnaDataSource(
        client_factory,
        manager.ena_converter_factory,
        filter_factory.ena_filter_factory
    )

    manager.data_source = ena_ds

    return ena_ds


def create_ena_datasource_from_config(
    ena_url: str,
    config: Dict
) -> EnaDataSource:
    """
    Instantiates `EnaDataSource` using the given `config`.
    """

    return create_ena_datasource(
        ena_url,
        config['user'],
        config['password'],
        config['contact_name'],
        config['contact_email']
    )
