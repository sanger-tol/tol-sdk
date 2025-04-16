# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Callable, Iterable, Optional

from .client import LabwhereApiClient
from .converter import (
    LabwhereApiConverter
)
from ..core import DataObject, DataSource, DataSourceError
from ..core.operator import (
    DetailGetter,
    Relational
)
from ..core.relationship import RelationshipConfig


ClientFactory = Callable[[], LabwhereApiClient]
LabwhereConverterFactory = Callable[[], LabwhereApiConverter]


class LabwhereDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    Relational
):
    """
    A `DataSource` that connects to a remote LabWhere API.

    Developers should likely use `create_labwhere_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        labwhere_converter_factory: LabwhereConverterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__lc_factory = labwhere_converter_factory
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'location': {
                'name': 'str',
                'parent': 'str',
                'container': 'bool',
                'status': 'str',
                'rows': 'int',
                'columns': 'int',
                'parentage': 'str',
                'location_type_id': 'int',
                'created_at': 'datetime',
                'updated_at': 'datetime'
            },
            'location_type': {
                'name': 'str',
                'created_at': 'datetime',
                'updated_at': 'datetime'
            }
        }

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        rc_location = RelationshipConfig()
        rc_location.to_one = {
            'parent_location': 'location',
            'location_type': 'location_type'
        }
        # rc_location.to_many = {'child_locations': 'location'}
        rc_location_type = RelationshipConfig()
        # rc_location_type.to_many = {'locations': 'location'}
        return {
            'location': rc_location,
            'location_type': rc_location_type
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
        labwhere_responses = (
            client.get_detail(object_type, id_)
            for id_ in object_ids
        )
        labwhere_converter = self.__lc_factory()
        return (
            labwhere_converter.convert(r)
            if r is not None else None
            for r in labwhere_responses
        )

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:

        if source.type == 'location' and relationship_name == 'parent_location':
            if source.parent is not None:
                parentage_ids = source.parent.split('/')
                parent_id = parentage_ids[len(parentage_ids) - 1]
                if parent_id != 'Empty':
                    return self.get_one(
                        'location',
                        parent_id
                    )
        if source.type == 'location' and relationship_name == 'location_type':
            if source.location_type_id is not None:
                return self.get_one(
                    'location_type',
                    source.location_type_id
                )

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:

        return []
