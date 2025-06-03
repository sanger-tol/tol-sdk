# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.elastic import ElasticDataSource

from ..dec import against
from ..fixtures import elastic


class TestSummarise:
    """
    Tests `ElasticDataSource` summarise methods
    for real `DataSource` instances.
    """

    @against(elastic)
    def test_summarise(
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

        # summarise all
        data_source.summarise_all([summary_obj])
        ds_sleep(5)

        rel_obj = data_source.get_one(
            'related',
            'related_summarise'
        )
        assert rel_obj.summarise_one_root_int_column_min == 1
        assert rel_obj.summarise_one_root_int_column_max == 5

        # change the first `root` to be the biggest
        first_root_obj = data_source.get_one(
            'root',
            'root_1_indeed'
        )
        first_root_obj.int_column = 42
        data_source.upsert('root', [first_root_obj])
        ds_sleep(5)

        # re-summarise from just the changed `root` instance
        data_source.resummarise_by_ids(
            [summary_obj],
            source_object_type='root',
            source_object_ids=['root_1_indeed']
        )
        ds_sleep(5)

        rel_obj = data_source.get_one(
            'related',
            'related_summarise'
        )
        assert rel_obj.summarise_one_root_int_column_min == 2
        assert rel_obj.summarise_one_root_int_column_max == 42

    @against(elastic)
    def test_summarise_zero_counts(
        self,
        data_source: ElasticDataSource,
        ds_sleep
    ):
        """
        Test that count summarisation correctly handles zero counts.
        Creates destination objects that should have zero counts
        and verifies they get explicit 0 values instead of null.
        """

        rel_obj_1 = data_source.data_object_factory('related', 'related_with_data')
        rel_obj_2 = data_source.data_object_factory('related', 'related_without_data')
        rel_obj_3 = data_source.data_object_factory('related', 'related_also_without_data')

        data_source.upsert('related', [rel_obj_1, rel_obj_2, rel_obj_3])

        # root objects that only point to the first related object
        root_objs = [
            data_source.data_object_factory(
                'root',
                f'root_{i}_zero_test',
                {'int_column': i},
                to_one={'related_object': rel_obj_1}
            )
            for i in range(1, 4)
        ]
        data_source.upsert('root', root_objs)
        ds_sleep(5)

        summary_obj = self.__summary_obj(
            'zero_count_summary',
            {
                'source_object_type': 'root',
                'destination_object_type': 'related',
                'object_filters': {},
                'group_by': ['related_object.id'],
                'stats_fields': [],
                'stats': [],
                'prefix': 'zero_test',
            }
        )

        original_summarise = data_source._summarise

        try:
            data_source.summarise_all([summary_obj])
            ds_sleep(5)
        finally:
            data_source._summarise = original_summarise

        rel_with_data = data_source.get_one('related', 'related_with_data')
        rel_without_data = data_source.get_one('related', 'related_without_data')
        rel_also_without_data = data_source.get_one('related', 'related_also_without_data')

        assert rel_with_data is not None
        assert rel_with_data.zero_test_root_count == 3
        assert rel_without_data is not None
        assert rel_without_data.zero_test_root_count == 0
        assert rel_also_without_data is not None
        assert rel_also_without_data.zero_test_root_count == 0

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
