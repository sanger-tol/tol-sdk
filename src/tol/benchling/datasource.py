# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List, Optional

import psycopg2
from psycopg2.extensions import connection

from ..core import (
    CoreDataObject,
    DataObject,
    ReadOnlyDataSource,
    DataSourceConfig,
    unsupported
)

class BenchlingDataSource(ReadOnlyDataSource):
    """
    A (read-only) DataSource for getting objects in Benchling
    """

    def __init__(self, config: DataSourceConfig) -> None:
        super().__init__(
            config,
            [
                'username',
                'password',
                'database',
                'hostname',
                'port'
            ]
        )

    @property
    def supported_types(self) -> List[str]:
        return [
            'sequencing_requests',
        ]

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs
    ) -> Iterable[Optional[DataObject]]:
        with self.__get_connection() as conn:
            with conn.cursor() as cur:
                formatted_ids = "', '".join(object_ids)
                cur.execute(
                    f"""
                    SELECT c.barcode, t.tolid, t.tubewell_id
    FROM pacbio_sequencing_submission2$raw AS pbsum
    LEFT JOIN container$raw AS c ON pbsum.sample_tube_id = c.id
    LEFT JOIN container_content$raw AS cc ON pbsum.sample_tube_id = cc.container_id
    LEFT JOIN submission_samples$raw AS subsam ON cc.entity_id = subsam.id
    LEFT JOIN dna_extract$raw AS dna ON subsam.original_dna_extract = dna.id
    LEFT JOIN tissue_prep$raw AS tp ON dna.tissue_prep = tp.id
    LEFT JOIN tissue$raw AS t ON tp.tissue = t.id
    WHERE c.archived$ = 'FALSE'
        AND pbsum.archived$ = 'FALSE'
        AND subsam.archived$ = 'FALSE'
        AND dna.archived$ = 'FALSE'
        AND c.barcode in ('{formatted_ids}')
                    """
                )
                results = cur.fetchall()
                names = (
                    'id',
                    'tolid',
                    "TUBE_OR_WELL_ID",
                )
                result_dicts = [
                    {
                        k: v for k, v in zip(names, r)
                    }
                    for r in results
                ]
                data_objects = [
                    CoreDataObject(
                        object_type,
                        data=r_dict,
                        id_ = r_dict['id']
                    )
                    for r_dict in result_dicts
                ]
                data_objects_dict = {
                    d.id: d for d in data_objects
                }
                return [
                    data_objects_dict.get(object_id)
                    for object_id in object_ids
                ]

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass

    def __get_connection(self) -> connection:
        return psycopg2.connect(
            user=self.username,
            password=self.password,
            database=self.database,
            port=self.port,
            host=self.hostname
        )
