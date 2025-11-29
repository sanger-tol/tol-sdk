# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .api_datasource import ApiDataSource, DOConverterFactory, JsonConverterFactory
from .client import JsonApiClient
from .converter import DataObjectConverter, JsonApiConverter
from .filter import DefaultApiFilter
from .parser import DefaultParser
from ..core import DataSource, ReqFieldsTree


class _ApiDSDict(Mapping):
    def __init__(self, api_ds: ApiDataSource) -> None:
        self.__ds = api_ds

    def __getitem__(self, __k: str) -> ApiDataSource:
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

    - `DataObjectConverter`
    - `JsonApiConverter`
    """

    def __init__(self, prefix: str) -> None:
        self.__prefix = prefix
        self.__data_source: Optional[DataSource] = None

    @property
    def data_source(self) -> Optional[DataSource]:
        return self.__data_source

    @data_source.setter
    def data_source(self, ds: DataSource) -> None:
        self.__data_source = ds

    def do_converter_factory(self) -> DOConverterFactory:
        """
        Returns an instantiated `DataObjectConverter`.
        """

        return DataObjectConverter(self.__data_source, prefix=self.__prefix)

    def json_converter_factory(
        self,
        object_type: str | None = None,
        requested_fields: list[str] | None = None,
    ) -> JsonConverterFactory:
        """
        Returns an instantiated `JsonApiConverter`.
        """

        req_fields_tree = (
            ReqFieldsTree(
                object_type,
                self.__data_source,
                requested_fields=requested_fields,
            )
            if object_type
            else None
        )

        parser = DefaultParser(self.__ds_dict, req_fields_tree)
        return JsonApiConverter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _ApiDSDict(self.data_source)


def _get_client_factory(
    api_url: str,
    token: Optional[str],
    data_prefix: str,
    retries: int,
    status_forcelist: list[int],
    merge_collections: bool | None,
) -> Callable[[], JsonApiClient]:
    """
    A resonable default for creating
    a `JsonApiClient` instance
    """

    return lambda: JsonApiClient(
        api_url,
        token=token,
        data_prefix=data_prefix,
        retries=retries,
        status_forcelist=status_forcelist,
        merge_collections=merge_collections,
    )


def _filter_factory() -> DefaultApiFilter:
    return DefaultApiFilter()


def create_api_datasource(
    api_url: str,
    token: Optional[str] = None,
    data_prefix: str = '/data',
    retries: int = 5,
    status_forcelist: Optional[list[int]] = None,
    merge_collections: bool | None = None,
) -> ApiDataSource:
    """
    Instantiates `ApiDataSource` using the given:

    - `api_url`
    - `token` (optional)
    """

    client_factory = _get_client_factory(
        api_url,
        token=token,
        data_prefix=data_prefix,
        retries=retries,
        status_forcelist=status_forcelist,
        merge_collections=merge_collections,
    )
    manager = _ConverterFactory(data_prefix)

    api_ds = ApiDataSource(
        client_factory,
        manager.json_converter_factory,
        manager.do_converter_factory,
        _filter_factory,
    )

    manager.data_source = api_ds

    return api_ds
