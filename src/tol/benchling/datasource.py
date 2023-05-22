# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List, Optional

import psycopg2

from ..core import (
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
        conn = self.__get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.barcode, c.name, subsam.name$, dna.name$, t.tolid, t.tubewell_id
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
                """
            )
            return cur.fetchall()

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass

    def __get_connection(self):
        return psycopg2.connect(
            user=self.username,
            password=self.password,
            database=self.database,
            port=self.port,
            host=self.hostname
        )
