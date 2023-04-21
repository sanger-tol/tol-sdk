# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase, mock)

from tol.core import (
    DataObject,
    DataSourceError,
    DataSourceFilter
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


class TestElasticDataSource(TestCase):

    def test_upsert(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
        objects = [DataObject('run_data', {'id': 1, 'field1': 'value1',
                                           'field2': 'value2', 'datefield': dt}),
                   DataObject('run_data', {'id': 2, 'field1': 'value3', 'field2': 'value4'})]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x.id,
                                           field_prefix='')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 1,
                    'doc': {
                        'field1': 'value1',
                        'field2': 'value2',
                        'datefield': dt.isoformat(),
                        'tol_updated_at': dt.isoformat(),
                        'tol_checksum': 'abc123'
                    }}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 2,
                    'doc': {'field1': 'value3', 'field2': 'value4',
                            'tol_updated_at': dt.isoformat(),
                            'tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x.field1)
        eds.helpers.bulk.assert_called_once()

    def test_upsert_add_prefix_and_id(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
        objects = [DataObject('run_data', {'field1': 'value1', 'field2': 'value2'}),
                   DataObject('run_data', {'field1': 'value3', 'field2': 'value4'})]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x.field1,
                                           field_prefix='pre')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value1',
                    'doc': {'pre_field1': 'value1', 'pre_field2': 'value2',
                            'pre_tol_updated_at': dt.isoformat(),
                            'pre_tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value3',
                    'doc': {'pre_field1': 'value3', 'pre_field2': 'value4',
                            'pre_tol_updated_at': dt.isoformat(),
                            'pre_tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x.field1)
        eds.helpers.bulk.assert_called_once()

    def test_upsert_error(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        eds.helpers.bulk.return_value = (2, 1)
        with self.assertRaises(DataSourceError):
            eds.upsert('index', objects, id_func=lambda x: x.field1)

    def test_get_list(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
        eds.helpers.scan.return_value = [
            {'_source': {'field1': 'value1', 'field2': 'value2'}},
            {'_source': {'field1': 'value3', 'field2': 'value4'}}
        ]

        returned = eds.get_list('index')
        eds.helpers.scan.assert_called_once()
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2'}, first.attributes)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_list_page(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
        eds.es.search.return_value = {
            'hits': {
                'hits': [
                    {'_source': {'field1': 'value1', 'field2': 'value2'}},
                    {'_source': {'field1': 'value3', 'field2': 'value4'}}
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
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_by_id(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )
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
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4'}, second.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_build_query(self):
        eds = MockElasticDataSource(
            {'uri': 'test', 'user': 'user', 'password': 'password', 'index_prefix': 'test'}
        )

        self.assertIsNone(eds._build_elasticsearch_query(None))

        # Exact filtering
        object_filters = DataSourceFilter()
        object_filters.exact = {'field1': 'string1', 'field2': 3, 'field3': None}
        expected = {'bool': {'must': [{'match': {'field1': 'string1'}},
                                      {'match': {'field2': 3}}],
                             'must_not': [{'exists': {'field': 'field3'}}]}}
        self.assertEqual(expected, eds._build_elasticsearch_query(object_filters))

        # Wildcard filtering
        object_filters = DataSourceFilter()
        object_filters.wildcard = {'field1': 'string1', 'field2': 'string2'}
        expected = {'bool': {'must': [
            {'wildcard': {'field1': {'value': 'string1*', 'boost': 1.0}}},
            {'wildcard': {'field2': {'value': 'string2*', 'boost': 1.0}}}],
            'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query(object_filters))

        # In list filtering
        object_filters = DataSourceFilter()
        object_filters.in_list = {'field1': ['string1', 'string2'],
                                  'field2': ['string3', 'string4']}
        expected = {'bool': {'must': [
            {'terms': {'field1': ['string1', 'string2'], 'boost': 1.0}},
            {'terms': {'field2': ['string3', 'string4'], 'boost': 1.0}}],
            'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query(object_filters))
