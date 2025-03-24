# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import GroupStatterDataLoader
from tol.elastic import ElasticDataSource

from ..dec import against
from ..fixtures import elastic


class TestSummariseObject:
    """
    Tests `ElasticDataSource.summarise_object()`
    for real `DataSource` instances.
    """

    @against(elastic)
    def test_after_remove(
        self,
        data_source: ElasticDataSource,
        ds_sleep
    ):
        """
        Insert data, summarise, remove an important
        one, re-summarise.
        """

        rel_obj = data_source.data_object_factory(
            'related',
            'related_summarise'
        )
        data_source.upsert('related', [rel_obj])

        root_objs = (
            data_source.data_object_factory(
                'root',
                f'root_{i}_indeed',
                {
                    'int_column': i
                }
            )
            for i in range(1, 6)
        )
        data_source.upsert('root', root_objs)

        ds_sleep(3)

        GroupStatterDataLoader(
            data_source,
            data_source,
            [],
            'related',
            'root',
            'summary_test',
            group_statter_group_by=['int_column']
        ).load('')
