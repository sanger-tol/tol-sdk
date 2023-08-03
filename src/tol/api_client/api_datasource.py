# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Iterable, Optional

from .client import AllRelationshipsDict, ApiClient, DefaultApiClient
from .dumper import Dumper, DefaultDumper
from .parser import Parser, DefaultParser
from ..api_base2.parser import JsonApiResource
from ..core import (
    DataObject,
    DataObjectFactory,
    DataSource,
    DataSourceFilter
)
from ..core.operator import (
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
)
from ..core.relationship import RelationshipConfig


ClientFactory = Callable[[str, str], ApiClient]
"""Takes a URL and token, returns an instance of `ApiClient`"""


def default_client_factory(url: str, key: str) -> DefaultApiClient:
    return DefaultApiClient(url, key)


DumperFactory = Callable[[], Dumper]
"""Returns a `Dumper` instance"""


def default_dumper_factory() -> DefaultDumper:
    return DefaultDumper()


ParserFactory = Callable[[DataObjectFactory], Parser]
"""Takes a `DataObjectFactory` callable, returns a `Parser`"""


def default_parser_factory(
    data_object_factory: DataObjectFactory
) -> DefaultParser:

    return DefaultParser(data_object_factory)


class ApiDataSource(
    DataSource,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
):
    """
    Communicates with a remote API.
    """

    def __init__(
        self,
        url: str,
        key: str,
        client_factory: ClientFactory = default_client_factory,
        dumper_factory: DumperFactory = default_dumper_factory,
        parser_factory: ParserFactory = default_parser_factory
    ) -> None:

        self.__url = url
        self.__key = key
        self.__client_factory = client_factory
        self.__dumper_factory = dumper_factory
        self.__parser_factory = parser_factory

    @property
    def supported_types(self) -> list[str]:
        client = self.__get_client()
        dump = client.get_operations_config()
        return list(dump.keys())

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        client = self.__get_client()
        dump = client.get_relationship_config()
        return self.__parse_relationship_config(dump)

    def get_attribute_types(self, object_type: str) -> dict:
        raise NotImplementedError()

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Iterable[Optional[DataObject]]:

        parser = self.__get_parser()
        results = self.__generate_detail(
            object_type,
            object_ids
        )
        return parser.convert_iterable(results)

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None
    ) -> Iterable[DataObject]:
        return super().get_list(object_type, object_filters)

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> tuple[Iterable[DataObject], int]:
        pass

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        return super().get_to_one_relation(source, relationship_name)

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:
        return super().get_to_many_relations(source, relationship_name)

    def __get_client(self) -> ApiClient:
        return self.__client_factory(
            self.__url,
            self.__key
        )

    def __get_parser(self) -> Parser:
        return self.__parser_factory(
            self.__data_object_factory
        )

    def __parse_relationship_config(
        self,
        dump: AllRelationshipsDict
    ) -> dict[str, RelationshipConfig]:

        return {
            k: RelationshipConfig(
                to_one=v.get('to_one'),
                to_many=v.get('to_many')
            )
            for k, v in dump.items()
        }

    def __generate_detail(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Iterable[JsonApiResource]:

        client = self.__get_client()
        return (
            client.get_detail(object_type, id_)
            for id_ in object_ids
        )
