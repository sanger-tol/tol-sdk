# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, List, Optional

from more_itertools import seekable

from .client import GoatApiClient
from .converter import (
    GoatApiConverter
)
from .filter import (
    GoatFilter
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

ClientFactory = Callable[[], GoatApiClient]
FilterFactory = Callable[[], GoatFilter]
GoatConverterFactory = Callable[[], GoatApiConverter]


class GoatDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
):
    """
    A `DataSource` that connects to a remote GoaT API.

    Developers should likely use `create_goat_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        goat_converter_factory: GoatConverterFactory,
        filter_factory: FilterFactory,
    ) -> None:

        self.__client_factory = client_factory
        self.__gc_factory = goat_converter_factory
        self.__filter_factory = filter_factory
        super().__init__({})

    def __get_filter_string(
        self,
        object_filters: Optional[DataSourceFilter]
    ) -> Optional[str]:

        if object_filters is None:
            return ''
        return self.__filter_factory().dumps(object_filters)

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'taxon': {
                'scientific_name': 'str',
                'common_name': 'str',
                'synonym': 'List[str]',
                'tolid_prefix': 'str',
                'assembly_level': 'str',
                'genome_size': 'int',
                'chromosome_number': 'int',
                'haploid_number': 'int',
                'ploidy': 'int',
                'echabs92': 'str',
                'habreg_2017': 'str',
                'marhabreg-2017': 'str',
                'waca_1981': 'str',
                'isb_wildlife_act_1976': 'str',
                'protection_of_badgers_act_1992': 'str',
                'family_representative': 'List[str]',
                'lineage': 'List[str]',
                'sample_collected': 'List[str]',
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        client = self.__client_factory()
        goat_response, _ = client.get_detail(object_type, object_ids)
        goat_converter = self.__gc_factory()

        converted_objects, _ = goat_converter.convert_list(goat_response) \
            if goat_response is not None else ([], 0)
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
        objects, total = self.__client_factory().get_list_page(
            object_type,
            page=page_number,
            page_size=page_size,
            filter_string=filter_string,
            sort_by=sort_by
        )
        converted_objects, _ = self.__gc_factory().convert_list(objects)
        return converted_objects, total

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        # There is no way to page beyond 10000 in GoaT. After discussions with GoaT they
        # users to set off long queries. Therefore, we just set a large size and no offset here.
        filter_string = self.__get_filter_string(object_filters)
        objects, total = self.__client_factory().get_list_page(
            object_type,
            page_size=10000000,  # large enough not to matter
            filter_string=filter_string,
        )
        converted_objects, _ = self.__gc_factory().convert_list(objects)
        return iter(converted_objects)

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        rc_taxon = RelationshipConfig()
        rc_taxon.to_one = {
            rank: 'taxon'
            for rank in self.get_ranks()
        }
        return {
            'taxon': rc_taxon
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

    def get_ranks(self) -> List[str]:
        return ['species', 'genus', 'family', 'order', 'class',
                'phylum', 'kingdom', 'superkingdom']
