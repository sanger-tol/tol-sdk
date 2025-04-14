# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, Optional

from .client import CopoApiClient
from .converter import (
    CopoApiConverter
)
from ..core import DataObject, DataSource, DataSourceError, DataSourceFilter
from ..core.operator import (
    DetailGetter,
    ListGetter,
    Relational
)
from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


ClientFactory = Callable[[], CopoApiClient]
CopoConverterFactory = Callable[[], CopoApiConverter]


class CopoDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter,
    Relational
):
    """
    A `DataSource` that connects to a remote COPO API.

    Developers should likely use `create_copo_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        copo_converter_factory: CopoConverterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__lc_factory = copo_converter_factory
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'manifest': {
            },
            'sample': {
                'associated_tol_project': 'str',
                'biosampleAccession': 'str',
                'copo_id': 'str',
                'copo_profile_title': 'str',
                'manifest_id': 'str',
                'manifest_version': '',
                'public_name': 'str',
                'sampleDerivedFrom': 'str',
                'sampleSameAs': 'str',
                'sampleSymbiontOf': 'str',
                'sraAccession': 'str',
                'status': 'str',
                'submissionAccession': 'str',
                'time_created': 'datetime',
                'time_updated': 'datetime',
                'tol_project': 'str'
            }
        }

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'manifest': 'manifest'
        }
        rc_manifest = RelationshipConfig()
        rc_manifest.to_many = {'samples': 'sample'}
        return {
            'sample': rc_sample,
            'manifest': rc_manifest
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
        copo_responses = client.get_detail(object_type, object_ids)
        copo_converter = self.__lc_factory()
        return (
            copo_converter.convert(r)
            if r is not None else None
            for r in copo_responses
        )

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        """
        This is a very limited implementation of `get_list`.
        It only supports checking for manifests in a project
        between certain dates
        """
        client = self.__client_factory()
        jc_converter = self.__lc_factory()

        project = object_filters.and_ \
            .get('project', {}) \
            .get('eq', {}) \
            .get('value', None)
        from_ = object_filters.and_ \
            .get('time_created', {}) \
            .get('gte', {}) \
            .get('value', None)
        to = object_filters.and_ \
            .get('time_created', {}) \
            .get('lt', {}) \
            .get('value', None)

        manifests_json = client.get_manifests(
            project=project,
            from_=from_,
            to=to,
        )
        manifests, _ = jc_converter.convert_list(manifests_json)
        return manifests

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:

        if source.type == 'sample' and relationship_name == 'manifest':
            if source.manifest_id is not None:
                return self.get_one(
                    'manifest',
                    source.manifest_id
                )

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:
        if source.type == 'manifest' and relationship_name == 'samples':
            client = self.__client_factory()
            copo_responses = client.get_samples_in_manifest(source.id)
            copo_converter = self.__lc_factory()
            return (
                copo_converter.convert(r)
                if r is not None else None
                for r in copo_responses
            )
