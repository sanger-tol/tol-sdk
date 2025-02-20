# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import json
from io import BytesIO
from typing import Dict, Iterable, Optional

from functools import cache

from minio import Minio


from ..json import S3JsonDataSource

from ..core import (
    DataSourceError,
    DataObject,
)

from ..core.operator import Relational

from ..core.relationship import RelationshipConfig




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
        rc_pipeline = RelationshipConfig()
        rc_pipeline.to_many = {
            'pipeline': 'pipeline'
        }
        return {
            'pipeline': rc_pipeline
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        return None

    def get_to_many_relations(
        self,
        source: DataObject
    ) -> Iterable[DataObject]:
        temp_config = {
            'uri': 's3://tol-system-test-assets/test.json',#f's3://gap/{source.id}/data/analysis.json',
            'type': 'pipeline',
            'id_attribute': 'id',
            'mappings': {
            },
            's3_host': 'cog.sanger.ac.uk',
            's3_access_key': self.config['s3_access_key'],
            's3_secret_key': self.config['s3_secret_key']
        }
        temp_ds = S3JsonDataSource(config=temp_config, secure=True)
        
        return temp_ds.get_list('pipeline')