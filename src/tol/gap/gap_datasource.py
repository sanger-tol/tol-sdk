# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from functools import cache
from typing import Dict, Iterable, Optional

from ..core import (
    DataObject,
    core_data_object
)
from ..core.operator import Relational
from ..core.relationship import RelationshipConfig
from ..json import S3JsonDataSource


class GapDataSource(
    S3JsonDataSource,
    Relational
):
    def __init__(
        self,
        config: Dict,
        secure: bool = True
    ) -> None:
        super().__init__(
            config=config,
            secure=secure
        )

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        rc_assembly = RelationshipConfig()
        rc_assembly.to_many = {
            'pipelines': 'pipeline',
            'assembly_details': 'assembly_detail'
        }
        return {
            'assembly': rc_assembly
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        return None

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
    ) -> Iterable[DataObject]:
        if relationship_name == 'pipelines':
            temp_config = {
                'uri': f's3://gap/{source.id}/data/analysis.json',
                'type': 'pipeline',
                'id_attribute': 'pipeline',
                'mappings': {
                    'pipeline': {
                        'heading': 'pipeline',
                        'type': 'str'
                    },
                    'analysis': {
                        'heading': 'analysis',
                        'type': 'str'
                    },
                    'results': {
                        'heading': 'results',
                        'type': 'str'
                    },
                    'description': {
                        'heading': 'description',
                        'type': 'str'
                    },
                    's3': {
                        'heading': 's3',
                        'type': 'str'
                    },
                    'lustre_path_analysis': {
                        'heading': 'lustre_path_analysis',
                        'type': 'str'
                    },
                },
                's3_host': 'cog.sanger.ac.uk',
                's3_access_key': None,
                's3_secret_key': None
            }
            temp_ds = S3JsonDataSource(config=temp_config, secure=True)
            cdo = core_data_object(temp_ds) # noqa
            return temp_ds.get_list('pipeline')

        elif relationship_name == 'assembly_details':
            temp_config = {
                'uri': f's3://gap/{source.id}/data/assembly.json',
                'type': 'assembly_detail',
                'id_attribute': 'name',
                'mappings': {
                    'name': {
                        'heading': 'name',
                        'type': 'str'
                    },
                    'info': {
                        'heading': 'info',
                        'type': 'str'
                    },
                },
                's3_host': 'cog.sanger.ac.uk',
                's3_access_key': None,
                's3_secret_key': None
            }
            temp_ds = S3JsonDataSource(config=temp_config, secure=True)
            cdo = core_data_object(temp_ds) # noqa
            return temp_ds.get_list('assembly_detail')
