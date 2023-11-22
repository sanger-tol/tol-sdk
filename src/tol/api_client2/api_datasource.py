# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import chain
from typing import Callable, Iterable, Optional

from .client import JsonApiClient
from .converter import (
    DataObjectConverter,
    JsonApiConverter
)
from .filter import ApiFilter
from .validate import validate
from ..api_base2.misc.operator_config import OperatorDict
from ..core import DataObject, DataSource, DataSourceFilter
from ..core.operator import (
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Upserter
)


ClientFactory = Callable[[], JsonApiClient]
JsonConverterFactory = Callable[[], JsonApiConverter]
DOConverterFactory = Callable[[], DataObjectConverter]
FilterFactory = Callable[[], ApiFilter]


class ApiDataSource(
    DataSource,

    # the supported operators
    Deleter,
    DetailGetter,
    PageGetter,
    ListGetter,
    Upserter
):
    """
    A `DataSource` that connects to a remote API based upon
    `api_base2`.

    Developers should likely use `create_api_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        json_converter_factory: JsonConverterFactory,
        do_converter_factory: DOConverterFactory,
        filter_factory: FilterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__jc_factory = json_converter_factory
        self.__dc_factory = do_converter_factory
        self.__filter_factory = filter_factory
        super().__init__({})

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        client = self.__client_factory()
        return client.config_attribute_types()

    @property
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    @validate('detailGet')
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Iterable[Optional[DataObject]]:

        client = self.__client_factory()
        json_responses = (
            client.get_detail(object_type, id_)
            for id_ in object_ids
        )
        json_converter = self.__jc_factory()
        return (
            json_converter.convert(r)
            if r is not None else None
            for r in json_responses
        )

    @validate('listGet')
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> tuple[Iterable[DataObject], int]:

        filter_string = self.__get_filter_string(object_filters)
        transfer = self.__client_factory().get_list_page(
            object_type,
            page_number,
            page_size,
            filter_string=filter_string,
            sort_string=sort_by
        )
        return self.__jc_factory().convert_list(transfer)

    @validate('listGet')
    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None
    ) -> Iterable[DataObject]:

        page = 1
        client = self.__client_factory()
        jc_converter = self.__jc_factory()
        filter_string = self.__get_filter_string(object_filters)

        while True:
            transfer = client.get_list_page(
                object_type,
                page,
                self.get_page_size(),
                filter_string=filter_string
            )
            (results_page, _) = jc_converter.convert_list(transfer)

            if not results_page:
                return

            yield from results_page
            page += 1

    @validate('delete')
    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> None:

        client = self.__client_factory()
        for object_id in object_ids:
            client.delete(object_type, object_id)

    @validate('upsert')
    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject]
    ) -> None:

        transfer = self.__dc_factory().convert_list(
            list(objects)
        )
        self.__client_factory().upsert(object_type, transfer)

    @property
    def supported_operations(self) -> dict[str, list[str]]:
        """
        The list of `Operator` ABC's implemented for each
        `object_type`.
        """

        client = self.__client_factory()
        transfer = client.config_operations()
        return self.__parse_operations(transfer)

    def __get_filter_string(
        self,
        object_filters: Optional[DataSourceFilter]
    ) -> Optional[str]:

        if object_filters is None:
            return None
        return self.__filter_factory().dumps(object_filters)

    def __parse_operations(
        self,
        transfer: dict[str, OperatorDict]
    ) -> dict[str, list[str]]:

        return {
            t: self.__join_operations(o)
            for t, o in transfer.items()
        }

    def __join_operations(
        self,
        operator_dict: OperatorDict
    ) -> list[str]:

        operators = chain(*list(operator_dict.values()))
        return list(operators)
