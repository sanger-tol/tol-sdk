# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, Optional

from cachetools.func import ttl_cache

from more_itertools import seekable

from .client import JiraClient
from .converter import (
    JiraConverter
)
from .filter import (
    JiraFilter
)
from .sort import (
    JiraSorter
)
from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import (
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
)
from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession

ClientFactory = Callable[[], JiraClient]
FilterFactory = Callable[[], JiraFilter]
SorterFactory = Callable[[], JiraSorter]
JiraConverterFactory = Callable[[], JiraConverter]


class JiraDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
):
    """
    A `DataSource` that connects to a remote JIRA

    Developers should likely use `create_jira_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        jira_converter_factory: JiraConverterFactory,
        filter_factory: FilterFactory,
        sorter_factory: SorterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__jc_factory = jira_converter_factory
        self.__filter_factory = filter_factory
        self.__sorter_factory = sorter_factory
        super().__init__({})
        self.DEFAULT_PAGE_SIZE = 100

    @ttl_cache(ttl=60)
    def get_fields(self) -> dict:
        return self.__client_factory().get_fields()

    def __get_filter_string(
        self,
        object_filters: Optional[DataSourceFilter]
    ) -> Optional[str]:

        if object_filters is None:
            return ''
        return self.__filter_factory().dumps(object_filters)

    def __get_sort_string(
        self,
        sort_by: Optional[str]
    ) -> str:
        return self.__sorter_factory().sort(sort_by)

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        fields = self.get_fields()
        return {
            'issue': {
                field['system_name']: field['type']
                for _, field in fields.items()
                if field['relation'] is None
            } | {
                'status_changes': 'List[Dict[str, Any]]'
            },
            'user': {
                'name': 'str',
                'emailAddress': 'str',
                'displayName': 'str'
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(self.attribute_types.keys())

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        client = self.__client_factory()
        jira_response = client.get_detail(object_type, object_ids)
        jira_converter = self.__jc_factory()

        converted_objects, _ = jira_converter.convert_list(jira_response) \
            if jira_response is not None else ([], 0)
        seekable_objects = seekable(converted_objects)
        for id_ in object_ids:
            seekable_objects.seek(0)
            for obj in seekable_objects:
                if obj.id == id_:
                    yield obj
                    break
            else:
                yield None

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None,
        session: Optional[OperableSession] = None
    ) -> tuple[Iterable[DataObject], int]:
        if page_size is None:
            page_size = self.get_page_size()
        filter_string = self.__get_filter_string(object_filters)
        sort_string = self.__get_sort_string(sort_by)
        issues, total = self.__client_factory().get_list_page(
            object_type,
            page=page_number,
            page_size=page_size,
            filter_string=f'{filter_string} {sort_string}'.strip()
        )
        converted_issues, _ = self.__jc_factory().convert_list(issues)
        return converted_issues, total

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:

        page = 1
        page_size = self.get_page_size()
        client = self.__client_factory()
        jc_converter = self.__jc_factory()
        filter_string = self.__get_filter_string(object_filters)

        while True:
            issues, _ = client.get_list_page(
                object_type,
                page,
                page_size,
                filter_string=filter_string + ' ' + self.__get_sort_string(None)
            )
            (results_page, _) = jc_converter.convert_list(issues)

            yield from results_page
            if len(results_page) < page_size:
                break

            page += 1

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        field_mappings = self.get_fields()
        return {
            'issue': RelationshipConfig(
                to_one={
                    field['system_name']: field['relation']
                    for _, field in field_mappings.items()
                    if field['relation'] is not None
                }
            )
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        # If we are here then the relationship has not been initialised
        return None

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:
        return []
