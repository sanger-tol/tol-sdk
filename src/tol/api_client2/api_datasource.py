# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from itertools import chain
from typing import Callable, Iterable, List, Optional

from .client import JsonApiClient
from .converter import (
    DataObjectConverter,
    JsonApiConverter
)
from .filter import ApiFilter
from .validate import validate, validate_id
from ..core import DataObject, DataSource, DataSourceFilter
from ..core.operator import (
    Counter,
    Deleter,
    DetailGetter,
    ListGetter,
    OperatorDict,
    PageGetter,
    Relational,
    Statter,
    Upserter
)
from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


ClientFactory = Callable[[], JsonApiClient]
JsonConverterFactory = Callable[[], JsonApiConverter]
DOConverterFactory = Callable[[], DataObjectConverter]
FilterFactory = Callable[[], ApiFilter]


class ApiDataSource(
    DataSource,

    # the supported operators
    Counter,
    Deleter,
    DetailGetter,
    PageGetter,
    ListGetter,
    Relational,
    Statter,
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
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        client = self.__client_factory()
        return client.config_attribute_types()

    @property
    @cache
    def attribute_metadata(self) -> dict[str, dict[str, dict[str, str | bool]]]:
        client = self.__client_factory()
        return client.config_attribute_metadata()

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        transfer = self.__client_factory().config_relationships()
        return self.__jc_factory().convert_relationship_config(
            transfer
        )

    @validate('detailGet')
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None
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
        sort_by: Optional[str] = None,
        session: Optional[OperableSession] = None
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
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
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

    @validate('count')
    def get_count(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> int:
        filter_string = self.__get_filter_string(object_filters)
        transfer = self.__client_factory().get_count(
            object_type,
            filter_string=filter_string
        )
        return self.__jc_factory().convert_count(transfer)

    @validate('stats')
    def get_stats(
        self,
        object_type: str,
        stats: Optional[List[str]] = [],
        stats_fields: Optional[List[str]] = [],
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> tuple[Iterable[DataObject], int]:

        filter_string = self.__get_filter_string(object_filters)
        transfer = self.__client_factory().get_stats(
            object_type,
            stats_string=','.join(stats),
            stats_fields_string=','.join(stats_fields),
            filter_string=filter_string
        )
        return self.__jc_factory().convert_stats(transfer)

    @validate('delete')
    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None
    ) -> None:

        client = self.__client_factory()
        for object_id in object_ids:
            client.delete(object_type, object_id)

    @validate('upsert')
    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs
    ) -> None:
        transfer = self.__dc_factory().convert_list(
            list(objects)
        )
        self.__client_factory().upsert(object_type, transfer)

    @validate('relational', direct_object=True)
    @validate_id
    def get_recursive_relation(
        self,
        source: DataObject,
        relationship_hops: list[str],
        session: Optional[OperableSession] = None
    ) -> Optional[DataObject]:

        self.validate_to_one_recurse(source.type, relationship_hops)
        transfer = self.__client_factory().get_to_one_relation_recursive(
            source.type,
            source.id,
            relationship_hops
        )
        if transfer is None:
            return None
        return self.__jc_factory().convert(transfer)

    @validate('relational', direct_object=True)
    @validate_id
    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[OperableSession] = None
    ) -> Optional[DataObject]:

        return self.get_recursive_relation(
            source,
            [relationship_name]
        )

    @validate('relational', direct_object=True)
    @validate_id
    def get_to_many_relations_page(
        self,
        source: DataObject,
        relationship_name: str,
        page: int,
        page_size: int,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:

        transfer = self.__client_factory().get_to_many_relations_page(
            source.type,
            source.id,
            relationship_name,
            page,
            page_size
        )
        return self.__jc_factory().convert_list(transfer)

    @validate('relational', direct_object=True)
    @validate_id
    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:

        page_number = 1
        page_size = self.get_page_size()

        while True:
            page, _ = self.get_to_many_relations_page(
                source,
                relationship_name,
                page_number,
                page_size
            )

            next_page = list(page)
            if not next_page:
                return

            yield from next_page
            if len(next_page) < page_size:
                return
            page_number += 1

    @property
    @cache
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
