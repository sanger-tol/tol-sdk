# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase, mock)

from tol.core import DataSourceError
from tol.elastic import ElasticDataSource


dt = datetime.fromtimestamp(1234567890)


class MockElasticDataSource(ElasticDataSource):
    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()

    def _add_updated(self, dict_):
        return {**dict_, 'tol_updated_at': dt}

    def _add_checksum(self, dict_):
        return {**dict_, 'tol_checksum': 'abc123'}


class TestElasticDataSource(TestCase):

    def test_upsert(self):
        eds = MockElasticDataSource({'uri': 'test', 'user': 'user', 'password': 'password'})
        objects = [{'id': 1, 'field1': 'value1', 'field2': 'value2'},
                   {'id': 2, 'field1': 'value3', 'field2': 'value4'}]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x['id'],
                                           field_prefix='')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 1,
                    'doc': {'id': 1, 'field1': 'value1', 'field2': 'value2',
                            'tol_updated_at': dt,
                            'tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 2,
                    'doc': {'id': 2, 'field1': 'value3', 'field2': 'value4',
                            'tol_updated_at': dt,
                            'tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x['field1'])
        eds.helpers.bulk.assert_called_once()

    def test_upsert_add_prefix_and_id(self):
        eds = MockElasticDataSource({'uri': 'test', 'user': 'user', 'password': 'password'})
        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        generator = eds._action_for_upsert('index', objects, id_func=lambda x: x['field1'],
                                           field_prefix='pre')
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value1',
                    'doc': {'pre_field1': 'value1', 'pre_field2': 'value2',
                            'pre_tol_updated_at': dt,
                            'pre_tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    'doc_as_upsert': True,
                    '_index': 'index',
                    '_id': 'value3',
                    'doc': {'pre_field1': 'value3', 'pre_field2': 'value4',
                            'pre_tol_updated_at': dt,
                            'pre_tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x['field1'])
        eds.helpers.bulk.assert_called_once()

    def test_upsert_error(self):
        eds = MockElasticDataSource({'uri': 'test', 'user': 'user', 'password': 'password'})
        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        eds.helpers.bulk.return_value = (2, 1)
        with self.assertRaises(DataSourceError):
            eds.upsert('index', objects, id_func=lambda x: x['field1'])

    def test_update(self):
        eds = MockElasticDataSource({'uri': 'test', 'user': 'user', 'password': 'password'})
        objects = [{'id': 1, 'field1': 'value1', 'field2': 'value2'},
                   {'id': 2, 'field1': 'value3', 'field2': 'value4'}]
        generator = eds._action_for_update('index', objects, id_func=lambda x: x['id'],
                                           field_prefix='')
        expected = {'_op_type': 'update',
                    '_index': 'index',
                    '_id': 1,
                    'doc': {'id': 1, 'field1': 'value1', 'field2': 'value2',
                            'tol_updated_at': dt,
                            'tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        expected = {'_op_type': 'update',
                    '_index': 'index',
                    '_id': 2,
                    'doc': {'id': 2, 'field1': 'value3', 'field2': 'value4',
                            'tol_updated_at': dt,
                            'tol_checksum': 'abc123'}}
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.update('index', objects, id_func=lambda x: x['field1'])
        eds.helpers.bulk.assert_called_once()

    def test_update_error(self):
        eds = MockElasticDataSource({'uri': 'test', 'user': 'user', 'password': 'password'})
        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        eds.helpers.bulk.return_value = (2, 1)
        with self.assertRaises(DataSourceError):
            eds.update('index', objects, id_func=lambda x: x['field1'])
