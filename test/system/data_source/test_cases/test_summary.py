# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
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
        data_source.upsert('related', [rel_obj], provenance='source1')

        root_objs = (
            data_source.data_object_factory(
                'root',
                f'root_{i}_indeed',
                attributes={
                    'int_column': i,
                    'str_column': str(i),
                    'datetime_column': datetime(2020, i, 1, 0, 0, 0),
                    'int_column_prov': i,
                    'str_column_prov': str(i),
                    'datetime_column_prov': datetime(2020, i, 1, 0, 0, 0)
                },
                to_one={
                    'related_object': rel_obj
                }
            )
            for i in range(1, 6)
        )
        data_source.upsert('root', root_objs, provenance='source1')

        ds_sleep(5)

        summary_obj = self.__summary_obj(
            'summary_one',
            {
                'source_object_type': 'root',
                'destination_object_type': 'related',
                'object_filters': {},
                'group_by': ['related_object.id'],
                'stats_fields': [
                    'int_column',
                    'str_column',
                    'datetime_column',
                    'int_column_prov',
                    'str_column_prov',
                    'datetime_column_prov',
                ],
                'provenance_override': 'source1',
                'stats': ['min', 'max'],
                'version': None
            }
        )

        # summarise all
        data_source.summarise_all([summary_obj])
        ds_sleep(5)

        rel_obj = data_source.get_one(
            'related',
            'related_summarise'
        )
        assert rel_obj.root_int_column_min == 1
        assert rel_obj.root_int_column_max == 5
        assert rel_obj.root_str_column_min == '1'
        assert rel_obj.root_str_column_max == '5'
        assert rel_obj.root_datetime_column_min == datetime(2020, 1, 1, 0, 0, 0)
        assert rel_obj.root_datetime_column_max == datetime(2020, 5, 1, 0, 0, 0)
        assert rel_obj.root_int_column_prov_min == 1
        assert rel_obj.root_int_column_prov_max == 5
        assert rel_obj.root_str_column_prov_min == '1'
        assert rel_obj.root_str_column_prov_max == '5'
        assert rel_obj.root_datetime_column_prov_min == datetime(2020, 1, 1, 0, 0, 0)
        assert rel_obj.root_datetime_column_prov_max == datetime(2020, 5, 1, 0, 0, 0)

        # change the first `root` to be the biggest
        first_root_obj = data_source.data_object_factory(
            'root',
            'root_1_indeed',
            attributes={
                'int_column': 42
            }
        )
        data_source.upsert('root', [first_root_obj], provenance='source1')
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
        assert rel_obj.root_int_column_min == 2
        assert rel_obj.root_int_column_max == 42

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
