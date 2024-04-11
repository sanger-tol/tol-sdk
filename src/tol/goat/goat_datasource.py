# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Callable, Iterable, List, Optional

from more_itertools import seekable

from .client import GoatApiClient
from .converter import (
    GoatApiConverter
)
from ..core import DataObject, DataSource, DataSourceError
from ..core.operator import (
    DetailGetter,
    Relational
)
from ..core.relationship import RelationshipConfig


ClientFactory = Callable[[], GoatApiClient]
GoatConverterFactory = Callable[[], GoatApiConverter]


class GoatDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
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
        goat_converter_factory: GoatConverterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__lc_factory = goat_converter_factory
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'taxon': {
                'scientific_name': 'str',
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
                'lineage': 'List[str]'
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
        object_ids: Iterable[str]
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        client = self.__client_factory()
        goat_response = client.get_detail(object_type, object_ids)
        goat_converter = self.__lc_factory()

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
