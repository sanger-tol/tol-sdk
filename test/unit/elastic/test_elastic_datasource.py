# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase, mock)

from tol.core import (
    DataSourceError,
    DataSourceFilter,
    core_data_object
)
from tol.elastic import ElasticDataSource


dt = datetime.fromtimestamp(1234567890)


class MockElasticDataSource(ElasticDataSource):
    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()

    def _add_updated(self, dict_):
        return {**dict_, 'tol_updated_at': dt.isoformat()}

    def _add_checksum(self, dict_):
        return {**dict_, 'tol_checksum': 'abc123'}

    def get_attribute_types(self, object_type: str):
        if object_type == 'obj_type':
            return {'field1': 'str',
                    'field2': 'str',
                    'datefield': 'date'}

    def get_attribute_types_super(self, object_type: str):
        return super().get_attribute_types(object_type)


def mock_elastic_data_source() -> ElasticDataSource:
    eds = MockElasticDataSource(
        {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
    )
    core_data_object_mock = core_data_object(eds)
    return core_data_object_mock, eds


class TestElasticDataSource(TestCase):

    def test_upsert(self):
        core_data_object, eds = mock_elastic_data_source()

        objects = [
            core_data_object(
                'obj_type',
                {
                    'id': 1,
                    'field1': 'value1',
                    'field2': 'value2',
                    'datefield': dt
                }
            ),
            core_data_object(
                'obj_type',
                {
                    'id': 2,
                    'field1': 'value3',
                    'field2': 'value4'
                }
            )
        ]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x.id,
                                           field_prefix='')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 1,
                    'doc': {'field1': 'value1', 'field2': 'value2',
                            'datefield': dt.isoformat(),
                            'tol_updated_at': dt.isoformat(),
                            'tol_checksum': 'abc123',
                            'uid': '1'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 2,
                    'doc': {'field1': 'value3', 'field2': 'value4',
                            'tol_updated_at': dt.isoformat(),
                            'tol_checksum': 'abc123',
                            'uid': '2'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x.field1)
        eds.helpers.bulk.assert_called_once()

    def test_upsert_add_prefix_and_id(self):
        CoreDataObject, eds = mock_elastic_data_source()  # noqa

        objects = [
            CoreDataObject(
                'obj_type',
                data={'field1': 'value1', 'field2': 'value2'}
            ),
            CoreDataObject(
                'obj_type',
                data={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x.field1,
                                           field_prefix='pre')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value1',
                    'doc': {'pre_field1': 'value1', 'pre_field2': 'value2',
                            'pre_tol_updated_at': dt.isoformat(),
                            'pre_tol_checksum': 'abc123',
                            'uid': 'value1'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value3',
                    'doc': {'pre_field1': 'value3', 'pre_field2': 'value4',
                            'pre_tol_updated_at': dt.isoformat(),
                            'pre_tol_checksum': 'abc123',
                            'uid': 'value3'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x.field1)
        eds.helpers.bulk.assert_called_once()

    def test_upsert_error(self):
        _, eds = mock_elastic_data_source()

        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        eds.helpers.bulk.return_value = (2, 1)
        with self.assertRaises(DataSourceError):
            eds.upsert('index', objects, id_func=lambda x: x.field1)

    def test_get_list(self):
        _, eds = mock_elastic_data_source()

        eds.helpers.scan.return_value = [
            {'_source': {'field1': 'value1', 'field2': 'value2'}, '_id': '1'},
            {'_source': {'field1': 'value3', 'field2': 'value4'}, '_id': '2'}
        ]

        returned = eds.get_list('index')
        eds.helpers.scan.assert_called_once()
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2'}, first.attributes)
        self.assertEqual('1', first.id)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        self.assertEqual('2', second.id)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_list_page(self):
        _, eds = mock_elastic_data_source()

        eds.es.search.return_value = {
            'hits': {
                'hits': [
                    {'_source': {'field1': 'value1', 'field2': 'value2'}, '_id': '1'},
                    {'_source': {'field1': 'value3', 'field2': 'value4'}, '_id': '2'}
                ],
                'total': {
                    'value': 2
                }
            }
        }

        returned, total = eds.get_list_page('index', 3)
        eds.es.search.assert_called_once()
        self.assertEqual(2, total)
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2'}, first.attributes)
        self.assertEqual('1', first.id)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        self.assertEqual('2', second.id)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_by_id(self):
        _, eds = mock_elastic_data_source()

        eds.es.mget.return_value = {
            'docs': [
                {
                    '_index': 'index',
                    '_id': '1',
                    '_source': {'field1': 'value1', 'field2': 'value2'}
                },
                {
                    '_index': 'index',
                    '_id': '2',
                    '_source': {'field1': 'value3', 'field2': 'value4'}
                }
            ]
        }

        returned = eds.get_by_id('index', ['1', '2'])
        eds.es.mget.assert_called_once()
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2'}, first.attributes)
        self.assertEqual('1', first.id)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        self.assertEqual('2', second.id)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_build_query(self):
        _, eds = mock_elastic_data_source()

        self.assertIsNone(eds._build_elasticsearch_query('obj_type', None))

        # Exact filtering
        object_filters = DataSourceFilter()
        object_filters.exact = {'field1': 'string1', 'field2': 3, 'field3': None}
        expected = {'bool': {'must': [{'match': {'field1.keyword': 'string1'}},
                                      {'match': {'field2.keyword': 3}}],
                             'must_not': [{'exists': {'field': 'field3'}}]}}
        self.assertEqual(expected, eds._build_elasticsearch_query('obj_type', object_filters))

        # Wildcard filtering
        object_filters = DataSourceFilter()
        object_filters.contains = {'field1': 'string1', 'field2': 'string2'}
        expected = {'bool': {'must': [
            {'wildcard': {'field1.keyword': {'value': 'string1*', 'boost': 1.0}}},
            {'wildcard': {'field2.keyword': {'value': 'string2*', 'boost': 1.0}}}],
            'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query('obj_type', object_filters))

        # In list filtering
        object_filters = DataSourceFilter()
        object_filters.in_list = {'field1': ['string1', 'string2'],
                                  'field2': ['string3', 'string4']}
        expected = {'bool': {'must': [
            {'terms': {'field1': ['string1', 'string2'], 'boost': 1.0}},
            {'terms': {'field2': ['string3', 'string4'], 'boost': 1.0}}],
            'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query('obj_type', object_filters))

        # Range filtering
        object_filters = DataSourceFilter()
        object_filters.range = {'field1': {'from': 'string1', 'to': 'string2'},
                                'datefield': {'from': '2022-01-01', 'to': '2023-01-01'}}
        expected = {'bool': {'must': [
            {'range': {'field1': {'gte': 'string1', 'lte': 'string2'}}},
            {'range': {'datefield': {'gte': '2022-01-01', 'lte': '2023-01-01'}}}],
            'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query('obj_type', object_filters))

    def test_build_sort(self):
        _, eds = mock_elastic_data_source()

        expected = [{'uid.keyword': 'asc'}]
        self.assertEqual(expected, eds._build_elasticsearch_sort('obj_type', None))

        # Asc
        sort_by = 'field1'
        expected = [{'field1.keyword': 'asc'}, {'uid.keyword': 'asc'}]
        self.assertEqual(expected, eds._build_elasticsearch_sort('obj_type', sort_by))

        # Desc
        sort_by = '-field1'
        expected = [{'field1.keyword': 'desc'}, {'uid.keyword': 'asc'}]
        self.assertEqual(expected, eds._build_elasticsearch_sort('obj_type', sort_by))

    def test_get_aggregations(self):
        _, eds = mock_elastic_data_source()

        agg_result = {
            'my-agg-name': {
                'doc_count_error_upper_bound': 0,
                'sum_other_doc_count': 0,
                'buckets': []
            }
        }
        eds.es.search.return_value = {
            'aggregations': agg_result
        }

        aggregations = {
            'my-agg-name': {
                'terms': {
                    'field': 'my-field'
                }
            }
        }
        returned = eds.get_aggregations('index',
                                        aggregations=aggregations)
        eds.es.search.assert_called_once()
        self.assertEqual(agg_result, returned)

    def test_get_supported_types(self):
        _, eds = mock_elastic_data_source()

        expected = ['index_1', 'index_2']
        eds.es.cat.indices.return_value = 'test-index-1\ntest-index-2'

        returned = eds.supported_types
        eds.es.cat.indices.assert_called_once()
        self.assertEqual(expected, returned)

    def test_get_attribute_types(self):
        _, eds = mock_elastic_data_source()

        eds.es.cat.indices.return_value = 'test-index-name'
        eds.es.indices.get_mapping.return_value = {
            'test-index-name': {
                'mappings': {
                    'properties': {
                        'field_1': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'type': 'keyword',
                                    'ignore_above': 256
                                }
                            }
                        },
                        'field_2': {
                            'type': 'date'
                        },
                        'field_3': {
                            'type': 'long'
                        }
                    }
                }
            }
        }
        expected = {'field_1': 'str',
                    'field_2': 'datetime',
                    'field_3': 'int'}
        returned = eds.get_attribute_types_super('index_name')
        eds.es.indices.get_mapping.assert_called_once()
        self.assertEqual(expected, returned)
