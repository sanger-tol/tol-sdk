# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .client import JiraClient
from .converter import (
    JiraConverter
)
from .filter import DefaultJiraFilter
from .jira_datasource import (
    JiraConverterFactory,
    JiraDataSource
)
from .parser import DefaultParser
from .sort import DefaultJiraSorter
from ..core import DataSource


class _BoldDSDict(Mapping):
    def __init__(self, api_ds: JiraDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> JiraDataSource:
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

    - `JiraConverter`
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

    @property
    def field_mappings(self) -> Optional[dict[str, dict[str, str]]]:
        return self.__field_mappings

    @field_mappings.setter
    def field_mappings(
        self,
        fm: dict[str, dict[str, str]]
    ) -> None:

        self.__field_mappings = fm

    def jira_converter_factory(self) -> JiraConverterFactory:
        """
        Returns an instantiated `JiraConverter`.
        """

        parser = DefaultParser(
            self.__ds_dict,
            self.__field_mappings)
        return JiraConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _BoldDSDict(self.data_source)


def _get_client_factory(
    api_url: str,
    api_key: str
) -> Callable[[], JiraClient]:
    """
    A resonable default for creating
    a `BoldApiClient` instance
    """

    return lambda: JiraClient(
        api_url,
        api_key
    )


class _FilterFactory:
    """
    Manges the instantation of:

    - `JiraFilter`
    """

    def __init__(self) -> None:
        self.__field_mappings: Optional[dict[str, dict[str, str]]] = None

    @property
    def field_mappings(self) -> Optional[dict[str, dict[str, str]]]:
        return self.__field_mappings

    @field_mappings.setter
    def field_mappings(
        self,
        fm: dict[str, dict[str, str]]
    ) -> None:

        self.__field_mappings = fm

    def jira_filter_factory(self) -> DefaultJiraFilter:
        """
        Returns an instantiated `JiraFilter`.
        """

        return DefaultJiraFilter(self.__field_mappings)


class _SorterFactory:
    """
    Manges the instantation of:

    - `JiraSorter`
    """

    def __init__(self) -> None:
        self.__field_mappings: Optional[dict[str, dict[str, str]]] = None

    @property
    def field_mappings(self) -> Optional[dict[str, dict[str, str]]]:
        return self.__field_mappings

    @field_mappings.setter
    def field_mappings(
        self,
        fm: dict[str, dict[str, str]]
    ) -> None:

        self.__field_mappings = fm

    def jira_sorter_factory(self) -> DefaultJiraFilter:
        """
        Returns an instantiated `JiraFilter`.
        """

        return DefaultJiraSorter(self.__field_mappings)


def create_jira_datasource(
    jira_url: str,
    jira_api_key: str
) -> JiraDataSource:
    """
    Instantiates `JiraDataSource` using the given:

    - `jira_url`
    - `jira_api_key`
    """

    client_factory = _get_client_factory(
        jira_url,
        jira_api_key
    )
    manager = _ConverterFactory()
    filter_factory = _FilterFactory()
    sorter_factory = _SorterFactory()

    jira_ds = JiraDataSource(
        client_factory,
        manager.jira_converter_factory,
        filter_factory.jira_filter_factory,
        sorter_factory.jira_sorter_factory
    )

    manager.data_source = jira_ds
    manager.field_mappings = jira_ds.get_fields()
    filter_factory.field_mappings = jira_ds.get_fields()
    sorter_factory.field_mappings = jira_ds.get_fields()

    return jira_ds
