# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import create_autospec

from tol.core import DataObject
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
                    'int_column': i,
                    'str_column': str(i)
                },
                to_one={
                    'related_object': rel_obj
                }
            )
            for i in range(1, 6)
        )
        data_source.upsert('root', root_objs)

        ds_sleep(5)

        summary_obj = self.__summary_obj(
            'summary_one',
            {
                'source_object_type': 'root',
                'destination_object_type': 'related',
                'object_filters': {},
                'group_by': ['related_object.id'],
                'stats_fields': ['int_column'],
                'stats': ['min', 'max'],
                'prefix': 'summarise_one',
            }
        )

        # make the 1st have the largest now
        data_source.summarise(
            'root',
            ['root_1_indeed'],
            [summary_obj]
        )
        ds_sleep(5)

        rel_obj = data_source.get_one(
            'related',
            'related_summarise'
        )
        import logging; logging.error(rel_obj.attributes); logging.error(rel_obj.root_int_column_min); assert False

    def __summary_obj(
        self,
        id_: str,
        attributes: dict[str, Any]
    ) -> DataObject:

        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'summary'
        mock_obj.id = id_
        mock_obj.attributes = attributes

        for k, v in attributes.items():
            setattr(mock_obj, k, v)

        return mock_obj
