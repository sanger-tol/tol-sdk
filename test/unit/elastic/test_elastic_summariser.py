# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Callable
from unittest import (TestCase, mock)

from tol.core import (
    DataSourceFilter,
    DefaultAttributeMetadata,
    core_data_object
)
from tol.core.relationship import RelationshipConfig
from tol.elastic import ElasticDataSource


dt = datetime.fromtimestamp(1234567890)


class MockElasticDataSourceSummariser(ElasticDataSource):

    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()
        self.helpers.bulk.return_value = (1, 0)
        self.es.cat.indices.return_value = 'test-custom-source test-custom-dest'

    def _add_updated(self, dict_):
        return {**dict_, 'tol_updated_at': dt.isoformat()}

    def _add_checksum(self, dict_):
        return {**dict_, 'tol_checksum': 'abc123'}

    def _mix_in_ext_and(self, object_filters, ext_and):
        if object_filters is None and ext_and is None:
            return None
        if object_filters is None:
            filter_obj = DataSourceFilter()
            filter_obj.and_ = ext_and
            return filter_obj
        if ext_and is None:
            return object_filters
        merged_filter = DataSourceFilter()
        merged_filter.and_ = {**object_filters.and_, **ext_and}
        return merged_filter

    @property
    def attribute_types(self):
        return {
            'custom_source': {
                'custom_field': 'str',
                'field1': 'str',
                'name': 'str',
                'status': 'str'
            },
            'custom_dest': {
                'id': 'str',
                'name': 'str'
            }
        }


class MockAttributeMetadataSummariser(DefaultAttributeMetadata):
    def is_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        return True


def mock_summariser_elastic_data_source() -> tuple[Callable, ElasticDataSource]:
    eds = MockElasticDataSourceSummariser({
        'uri': 'test',
        'user': 'user',
        'password': 'password',
        'index_prefix': 'test',
        'relationship_cfg': {
            'custom_source': RelationshipConfig(to_one={'custom_dest': 'custom_dest'}),
        },
        'runtime_fields': {}
    }, attribute_metadata=MockAttributeMetadataSummariser)

    return core_data_object(eds), eds


def create_mock_summary_object(core_data_object, **kwargs):
    default_attributes = {
        'source_object_type': 'custom_source',
        'destination_object_type': 'custom_dest',
        'group_by': ['custom_dest.id'],
        'stats_fields': [],
        'stats': [],
        'prefix': 'test',
        'object_filters': None
    }
    default_attributes.update(kwargs)

    summary = mock.Mock()
    for key, value in default_attributes.items():
        setattr(summary, key, value)

    return summary


class TestElasticSummariser(TestCase):
    def test_zero_count_flow(self):
        core_data_object, eds = mock_summariser_elastic_data_source()
        source_objects = [
            core_data_object('custom_source', id_='source1',
                             to_one={'custom_dest': core_data_object('custom_dest', id_='dest1')}),
            core_data_object('custom_source', id_='source2',
                             to_one={'custom_dest': core_data_object('custom_dest', id_='dest2')}),
            core_data_object('custom_source', id_='source3',
                             to_one={'custom_dest': core_data_object('custom_dest', id_='dest3')}),
        ]

        zero_count_destinations = [
            core_data_object('custom_dest', id_='dest3'),
        ]
        eds.get_list = mock.Mock(return_value=iter(source_objects))
        eds.get_by_id = mock.Mock(return_value=iter(zero_count_destinations))

        def mock_get_group_stats(*args, **kwargs):
            return iter([
                {'key': {'custom_dest.id': 'dest1'}, 'stats': {'count': 1}},
                {'key': {'custom_dest.id': 'dest2'}, 'stats': {'count': 1}}
            ])
        eds.get_group_stats = mock.Mock(side_effect=mock_get_group_stats)
        upserted_objects = []

        def track_upsert(object_type, objects, **kwargs):
            upserted_objects.extend(list(objects))
        eds.upsert = track_upsert
        summary = create_mock_summary_object(core_data_object, prefix='test')
        eds._summarise(summary)

        zero_count_objects = [obj for obj in upserted_objects
                      if (hasattr(obj, 'attributes')
                          and obj.attributes.get('custom_source_count') == 0)]

        self.assertEqual(len(zero_count_objects), 1)
        self.assertEqual(zero_count_objects[0].id, 'dest3')

    def test_non_count_summarisation_skips_zero_handling(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        eds.get_list = mock.Mock()
        eds.get_by_id = mock.Mock()

        summary = create_mock_summary_object(
            core_data_object,
            stats_fields=['field1'],
            stats=['sum', 'avg']
        )

        with mock.patch('tol.elastic.elastic_datasource.GroupStatterDataLoader') as mock_loader:
            mock_loader_instance = mock.Mock()
            mock_loader.return_value = mock_loader_instance
            eds._summarise(summary)

        eds.get_list.assert_not_called()
        eds.get_by_id.assert_not_called()
        mock_loader.assert_called_once()

    def test_get_all_destination_ids(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        destination_objects = [
            core_data_object('custom_dest', id_='dest1'),
            core_data_object('custom_dest', id_='dest2'),
            core_data_object('custom_dest', id_='dest3'),
        ]

        eds.get_list = mock.Mock(return_value=iter(destination_objects))
        summary = create_mock_summary_object(core_data_object)

        result = eds._get_all_destination_ids(summary)
        expected = {'dest1', 'dest2', 'dest3'}
        self.assertEqual(result, expected)
        eds.get_list.assert_called_once_with('custom_dest')

    def test_get_group_by_value_direct_attribute(self):
        core_data_object, eds = mock_summariser_elastic_data_source()
        obj = core_data_object('custom_source', id_='1',
                               attributes={'field1': 'test_value'})
        result = eds._get_group_by_value(obj, 'field1', 'custom_source')
        self.assertEqual(result, 'test_value')

    def test_get_group_by_value_relationship_id(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        obj = core_data_object('custom_source', id_='1',
                               to_one={'custom_dest':
                                       core_data_object('custom_dest', id_='dest1')})

        result = eds._get_group_by_value(obj, 'custom_dest.id', 'custom_source')
        self.assertEqual(result, 'dest1')

    def test_get_group_by_value_relationship_attribute(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        obj = core_data_object('custom_source', id_='1',
                               to_one={'custom_dest':
                                       core_data_object('custom_dest', id_='dest1',
                                                        attributes={'name': 'Human'})})

        result = eds._get_group_by_value(obj, 'custom_dest.name', 'custom_source')
        self.assertEqual(result, 'Human')

    def test_create_zero_count_objects(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        missing_ids = {'dest1', 'dest2'}
        destinations = [
            core_data_object('custom_dest', id_='dest1',
                             attributes={'name': 'Dest 1'}),
            core_data_object('custom_dest', id_='dest2',
                             attributes={'name': 'Dest 2'}),
        ]

        eds.get_by_id = mock.Mock(return_value=iter(destinations))

        upserted_objects = []

        def track_upsert(object_type, objects, **kwargs):
            upserted_objects.extend(list(objects))
            self.assertEqual(kwargs.get('field_prefix'), 'test')
        eds.upsert = track_upsert

        summary = create_mock_summary_object(core_data_object)
        eds._create_zero_count_objects(summary, missing_ids)

        self.assertEqual(len(upserted_objects), 2)

        for obj in upserted_objects:
            self.assertEqual(obj.attributes['custom_source_count'], 0)
            self.assertIn(obj.id, {'dest1', 'dest2'})

    def test_mix_in_ext_and_filters(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        result = eds._mix_in_ext_and(None, None)
        self.assertIsNone(result)

        ext_and = {'field1': {'eq': {'value': 'test'}}}
        result = eds._mix_in_ext_and(None, ext_and)
        self.assertEqual(result.and_, ext_and)

        object_filter = DataSourceFilter()
        object_filter.and_ = {'field2': {'eq': {'value': 'existing'}}}
        result = eds._mix_in_ext_and(object_filter, None)
        self.assertEqual(result, object_filter)

        result = eds._mix_in_ext_and(object_filter, ext_and)
        expected = {
            'field1': {'eq': {'value': 'test'}},
            'field2': {'eq': {'value': 'existing'}}
        }
        self.assertEqual(result.and_, expected)

    def test_summarise_with_ext_and_filters(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        eds.get_list = mock.Mock(return_value=iter([]))
        eds.get_by_id = mock.Mock(return_value=iter([]))

        def mock_get_group_stats(*args, **kwargs):
            return iter([])

        eds.get_group_stats = mock.Mock(side_effect=mock_get_group_stats)

        existing_filter = DataSourceFilter()
        existing_filter.and_ = {'field1': {'eq': {'value': 'existing'}}}

        summary = create_mock_summary_object(core_data_object, object_filters=existing_filter)
        ext_and = {'field2': {'eq': {'value': 'additional'}}}

        with mock.patch('tol.elastic.elastic_datasource.GroupStatterDataLoader') as mock_loader:
            mock_loader_instance = mock.Mock()
            mock_loader.return_value = mock_loader_instance

            eds.upsert = mock.Mock()
            eds._summarise(summary, ext_and=ext_and)

            call_args = mock_loader.call_args[1]
            merged_filters = call_args['object_filters']

            self.assertIn('field1', merged_filters.and_)
            self.assertIn('field2', merged_filters.and_)
            self.assertEqual(merged_filters.and_['field1'], {'eq': {'value': 'existing'}})
            self.assertEqual(merged_filters.and_['field2'], {'eq': {'value': 'additional'}})

    def test_loader_parameter(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        eds.get_list = mock.Mock(return_value=iter([]))
        eds.get_by_id = mock.Mock(return_value=iter([]))

        def mock_get_group_stats(*args, **kwargs):
            return iter([])

        eds.get_group_stats = mock.Mock(side_effect=mock_get_group_stats)

        custom_filter = DataSourceFilter()
        custom_filter.and_ = {'field1': {'eq': {'value': 'test'}}}

        summary = create_mock_summary_object(
            core_data_object,
            source_object_type='custom_source',
            destination_object_type='custom_dest',
            group_by=['custom_field'],
            stats_fields=[],
            stats=[],
            object_filters=custom_filter
        )

        with mock.patch('tol.elastic.elastic_datasource.GroupStatterDataLoader') as mock_loader:
            mock_loader_instance = mock.Mock()
            mock_loader.return_value = mock_loader_instance

            eds.upsert = mock.Mock()
            eds._summarise(summary)

            mock_loader.assert_called_once_with(
                eds,
                eds,
                [],
                'custom_source',
                'custom_dest',
                'Enhanced summariser with zero count handling',
                object_filters=custom_filter,
                group_statter_group_by=['custom_field'],
                group_statter_stats_fields=[],
                group_statter_stats=[]
            )

    def test_loader_parameter_non_count(self):
        core_data_object, eds = mock_summariser_elastic_data_source()

        eds.get_list = mock.Mock(return_value=iter([]))
        eds.get_by_id = mock.Mock(return_value=iter([]))

        custom_filter = DataSourceFilter()
        custom_filter.and_ = {'field1': {'eq': {'value': 'test'}}}

        summary = create_mock_summary_object(
            core_data_object,
            source_object_type='custom_source',
            destination_object_type='custom_dest',
            group_by=['custom_field'],
            stats_fields=['field1'],
            stats=['sum'],
            object_filters=custom_filter
        )

        with mock.patch('tol.elastic.elastic_datasource.GroupStatterDataLoader') as mock_loader:
            mock_loader_instance = mock.Mock()
            mock_loader.return_value = mock_loader_instance

            eds.upsert = mock.Mock()
            eds._summarise(summary)

            mock_loader.assert_called_once_with(
                eds,
                eds,
                [],
                'custom_source',
                'custom_dest',
                'Unmanaged summariser (no audit)',
                object_filters=custom_filter,
                group_statter_group_by=['custom_field'],
                group_statter_stats_fields=['field1'],
                group_statter_stats=['sum']
            )
