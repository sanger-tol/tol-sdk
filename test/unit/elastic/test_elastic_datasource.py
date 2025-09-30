# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Callable
from unittest import (TestCase, mock)

from tol.core import (
    DataObject,
    DataSourceError,
    DataSourceFilter,
    DefaultAttributeMetadata,
    core_data_object
)
from tol.core.relationship import RelationshipConfig
from tol.elastic import (
    ElasticDataSource,
    RuntimeField
)


dt = datetime.fromtimestamp(1234567890)


class MockElasticDataSource(ElasticDataSource):
    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()

        self.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'hidden-reltype': {'aliases': {'test-reltype': {}}}
        }
        self.index_prefix = 'test'

    @property
    def attribute_types(self):
        return {
            'obj_type': {
                'field1': 'str',
                'field2': 'str',
                'field3': 'int',
                'field4': 'str',
                'field5': 'str',
                'field6': 'int',
                'field7': 'str',
                'field8': 'datetime',
                'datefield': 'datetime'},
            'reltype': {
                'field3': 'str',
                'field4': 'str',
                'datefield': 'datetime'
            }
        }


class MockAttributeMetadata(DefaultAttributeMetadata):
    def is_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:

        if attribute_name in ['field1', 'field2']:
            return True
        return False


def mock_elastic_data_source() -> tuple[Callable, ElasticDataSource]:
    eds = MockElasticDataSource(
        {
            'uri': 'test',
            'user': 'user',
            'password': 'password',
            'index_prefix': 'test'
        },
        relationship_cfg={
            'obj_type': RelationshipConfig(
                to_one={'relationship': 'reltype'},
                to_many={'children': 'reltype'}
            ),
            'reltype': RelationshipConfig(
                to_one={'parent': 'obj_type'}
            )
        },
        runtime_fields={
            'obj_type': {
                'field7': RuntimeField(
                    field_type='keyword',
                    dependencies=[],
                    function_body="emit('Hello')"
                ),
                'field8': RuntimeField(
                    field_type='date',
                    dependencies=['datefield'],
                    function_body="emit(doc['datefield'].value.toEpochMilli())"
                )
            }
        },
        attribute_metadata=MockAttributeMetadata
    )
    core_data_object_mock = core_data_object(eds)
    return core_data_object_mock, eds


def mock_lazy_elastic_data_source() -> tuple[Callable, ElasticDataSource]:
    cdo, eds = mock_elastic_data_source()
    eds.lazy_fetch = True

    return cdo, eds


class TestUidSubstitution:
    """
    `uid` is a private attribute, put in place as a
    workaround of the limitations of ElasticSearch,
    regarding document `id` fields.

    `ElasticDataSource` must internally use `uid`, but
    expose this as `id` proper.
    """

    def test_sort_by_id(self):
        """
        `ElasticDataSource().get_list_page()` converts
        sort_by directives containing `id` to `uid`
        internally.
        """

        self.__test_uid_sort('-id', 'desc')
        self.__test_uid_sort('id', 'asc')

    def test_get_by_id(self):
        """
        `ElasticDataSource().get_by_id()` removes `uid`
        from elastic transfers
        """

        _, mock_ds = mock_elastic_data_source()

        mock_ds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': 'lol',
                '_source': {
                    'field1': 'train',
                    'uid': 'yes',
                }
            }
        ]

        (obj,) = list(
            mock_ds.get_by_id('obj_type', ['lol'])
        )

        assert 'uid' not in obj.attributes

    def __test_uid_sort(self, sort_by: str, order: str) -> None:

        _, mock_ds = mock_elastic_data_source()

        expected_sort = [
            {
                'uid.keyword': {
                    'order': order,
                    'unmapped_type': 'keyword'
                }
            }
        ]

        mock_ds.es.search.return_value = {
            'hits': {
                'hits': [],
                'total': {'value': 0}
            }
        }

        mock_ds.get_list_page(
            'obj_type',
            1,
            sort_by=sort_by
        )

        mock_ds.es.search.assert_called_once()

        (_, kwargs) = mock_ds.es.search.call_args_list[0]
        assert kwargs['sort'] == expected_sort


class TestElasticDataSource(TestCase):

    def test_upsert(self):
        core_data_object, eds = mock_elastic_data_source()

        objects = [
            core_data_object(
                'obj_type',
                id_=1,
                attributes={
                    'field1': 'value1',
                    'field2': 'value2',
                    'datefield': dt
                },
                to_one={
                    'relationship': core_data_object(
                        'reltype',
                        id_='rel1'
                    )
                }
            ),
            core_data_object(
                'obj_type',
                id_=2,
                attributes={
                    'field1': 'value3',
                    'field2': 'value4'
                }
            )
        ]
        generator = eds._action_for_upsert('test-obj-type', objects, id_func=lambda x: x.id,
                                           field_prefix='')
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 1,
            'script': {
                'source': eds._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field1': 'value1',
                        'field2': 'value2',
                        'datefield': dt.isoformat(),
                        'relationship': {
                            'id': 'rel1'
                        },
                        'uid': '1'
                    }
                }
            }
        }
        self.assertEqual(expected, next(generator))
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 2,
            'script': {
                'source': eds._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field1': 'value3',
                        'field2': 'value4',
                        'uid': '2'
                    }
                }
            }
        }
        self.assertEqual(expected, next(generator))
        eds.helpers.bulk.return_value = (2, 0)
        eds.upsert('index', objects, id_func=lambda x: x.field1)
        eds.helpers.bulk.assert_called_once()

    def test_upsert_add_prefix_and_id(self):
        CoreDataObject, eds = mock_elastic_data_source()  # noqa

        objects = [
            CoreDataObject(
                'obj_type',
                attributes={'field1': 'value1', 'field2': 'value2'}
            ),
            CoreDataObject(
                'obj_type',
                attributes={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        generator = eds._action_for_upsert('test-obj-type', objects, id_func=lambda x: x.field1,
                                           field_prefix='pre')
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 'value1',
            'script': {
                'source': eds._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'pre_field1': 'value1',
                        'pre_field2': 'value2',
                        'uid': 'value1'
                    }
                }
            }
        }
        self.assertEqual(expected, next(generator))
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 'value3',
            'script': {
                'source': eds._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'pre_field1': 'value3',
                        'pre_field2': 'value4',
                        'uid': 'value3'
                    }
                }
            }
        }
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
            eds.upsert('obj_type', objects, id_func=lambda x: x.field1)

    def test_update(self):
        core_data_object, eds = mock_elastic_data_source()

        update1 = {
            'field1': 'value1',
            'field2': 'value2',
            'relationship': core_data_object(
                'reltype',
                id_='rel1',
                attributes={'field3': 'string1', 'field4': 'string2'}
            )
        }

        update2 = {'field1': 'value3',
                   'field2': 'value4'}
        updates = [(None, update1),
                   (None, update2)]

        update_body = eds._action_for_update('obj_type',
                                             update1,
                                             field_prefix='',
                                             candidate_key=['field1'])
        expected = {
            'query': {
                'bool': {
                    'must': [{
                        'match': {'field1.keyword': 'value1'}
                    }],
                    'must_not': []
                }
            },
            'script': {
                'source': eds._update_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field2': 'value2',
                        'relationship': {
                            'id': 'rel1',
                            'field3': 'string1',
                            'field4': 'string2'
                        }
                    }
                }
            }
        }
        self.assertEqual(expected, update_body)
        eds.es.update_by_query.return_value = (2, 0)
        eds.update('obj_type', updates, candidate_key=['field1'])
        self.assertEqual(eds.es.update_by_query.call_count, 2)

    def test_get_list(self):
        _, eds = mock_elastic_data_source()

        eds.helpers.scan.return_value = [
            {'_source': {'field1': 'value1', 'field2': 'value2'},
             'fields': {'field7': ['Hello']},
             '_id': '1', '_index': 'test-obj-type'},
            {'_source': {'field1': 'value3', 'field2': 'value4'},
             'fields': {'field7': ['Hello']},
             '_id': '2', '_index': 'test-obj-type'}
        ]

        returned = eds.get_list('obj_type')
        eds.helpers.scan.assert_called_once()
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2', 'field7': 'Hello'},
                         first.attributes)
        self.assertEqual('1', first.id)
        self.assertEqual('obj_type', first.type)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4', 'field7': 'Hello'},
                         second.attributes)
        self.assertEqual('2', second.id)
        self.assertEqual('obj_type', second.type)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_list_page(self):
        _, eds = mock_elastic_data_source()

        eds.es.search.return_value = {
            'hits': {
                'hits': [
                    {'_source': {'field1': 'value1', 'field2': 'value2'},
                     'fields': {'field7': ['Hello']},
                     '_id': '1', '_index': 'test-obj-type'},
                    {'_source': {'field1': 'value3', 'field2': 'value4'},
                     'fields': {'field7': ['Hello']},
                     '_id': '2', '_index': 'test-obj-type'}
                ],
                'total': {
                    'value': 2
                }
            }
        }

        returned, total = eds.get_list_page('obj_type', 3)
        eds.es.search.assert_called_once()
        self.assertEqual(2, total)
        first = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2', 'field7': 'Hello'},
                         first.attributes)
        self.assertEqual('1', first.id)
        self.assertEqual('obj_type', first.type)
        second = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4', 'field7': 'Hello'},
                         second.attributes)
        self.assertEqual('2', second.id)
        self.assertEqual('obj_type', second.type)
        with self.assertRaises(StopIteration):
            next(returned)

    def test_get_by_id(self):
        _, eds = mock_elastic_data_source()

        eds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1',
                '_source': {'field1': 'value1', 'field2': 'value2'},
                'fields': {'field7': ['Hello']}
            },
            {
                '_index': 'test-obj-type',
                '_id': '2',
                '_source': {'field1': 'value3', 'field2': 'value4'},
                'fields': {'field7': ['Hello']},
            }
        ]

        returned = eds.get_by_id('obj_type', ['2', '1'])
        first = next(returned)
        self.assertEqual({'field1': 'value3', 'field2': 'value4', 'field7': 'Hello'},
                         first.attributes)
        self.assertEqual('2', first.id)
        self.assertEqual('obj_type', first.type)
        second = next(returned)
        self.assertEqual({'field1': 'value1', 'field2': 'value2', 'field7': 'Hello'},
                         second.attributes)
        self.assertEqual('1', second.id)
        self.assertEqual('obj_type', second.type)
        with self.assertRaises(StopIteration):
            next(returned)
        eds.helpers.scan.assert_called_once()

    def test_build_query(self):
        _, eds = mock_elastic_data_source()

        expected = {'bool': {'must': [], 'must_not': []}}
        self.assertEqual(expected, eds._build_elasticsearch_query('obj_type', None))

        # And filtering
        object_filters = DataSourceFilter()
        object_filters.and_ = {
            'field1': {
                'exists': {},
                'lt': {'field': 'field2'}
            },
            'field2': {
                'exists': {'negate': True}
            },
            'field3': {
                'lt': {'value': 16},
                'gte': {'value': 2}
            },
            'field4': {
                'contains': {'value': 'abc'}
            },
            'field5': {
                'in_list': {'value': ['one', 'two']}
            },
            'field6': {
                'eq': {'value': 5}
            },
            'field7': {
                'eq': {'value': 'haberdashery', 'negate': True}
            },
            'field8': {
                'gt': {'value': '2022-01-01'},
                'lte': {'value': '2023-01-01'}
            },
            'datefield': {
                'gt': {'value': '2022-01-01'},
                'lte': {'value': '2023-01-01'}
            },
            'relationship.field3': {
                'eq': {'value': 'string1'}
            }
        }
        expected = {
            'bool': {
                'must': [
                    {'exists': {'field': 'field1.keyword'}},
                    {'range': {'field3': {'lt': 16}}},
                    {'range': {'field3': {'gte': 2}}},
                    {'wildcard': {'field4.keyword': {'value': 'abc*', 'boost': 1.0}}},
                    {'terms': {'field5.keyword': ['one', 'two'], 'boost': 1.0}},
                    {'match': {'field6': 5}},
                    {'range': {'field8': {'gt': datetime(2022, 1, 1, 0, 0)}}},
                    {'range': {'field8': {'lte': datetime(2023, 1, 1, 0, 0)}}},
                    {'range': {'datefield': {'gt': datetime(2022, 1, 1, 0, 0)}}},
                    {'range': {'datefield': {'lte': datetime(2023, 1, 1, 0, 0)}}},
                    {'match': {'relationship.field3.keyword': 'string1'}}
                ],
                'must_not': [
                    {'exists': {'field': 'field2.keyword'}},
                    {'match': {'field7': 'haberdashery'}}
                ],
                'filter': eds._get_field_comparison_filter(
                    'field1.keyword', 'field2.keyword', 'lt', False
                )
            }
        }

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

    def test_get_count(self):
        _, eds = mock_elastic_data_source()

        eds.es.search.return_value = {
            'hits': {
                'total': {
                    'value': 12345
                }
            }
        }

        returned = eds.get_count('obj_type')
        eds.es.search.assert_called_once()
        self.assertEqual(12345, returned)

    def test_get_stats_unique_and_cardinality(self):
        _, eds = mock_elastic_data_source()

        ret = {
            'aggregations': {
                'datefield_unique': {
                    'value': 10
                },
                'datefield_cardinality': {
                    'value': 15
                },
                'field2_unique': {
                    'value': 3
                },
                'field2_cardinality': {
                    'value': 5
                }
            }
        }
        eds.es.search.side_effect = [
            ret
        ]

        returned = eds.get_stats(
            'obj_type',
            stats_fields=['field2', 'datefield'],
            stats=['unique', 'cardinality']
        )
        self.assertEqual({
            'stats': {
                'datefield': {
                    'unique': 10,
                    'cardinality': 15
                },
                'field2': {
                    'unique': 3,
                    'cardinality': 5
                }
            }
        }, returned)
        self.assertEqual(eds.es.search.call_count, 1)

    def test_get_group_stats_standard(self):
        _, eds = mock_elastic_data_source()

        first_ret = {
            'aggregations': {
                'counts': {
                    'after_key': {
                        'field1': '1234'
                    },
                    'buckets': [
                        {
                            'key': {
                                'field1': '1111'
                            },
                            'doc_count': 20,
                            'datefield_min': {
                                'value': 1000000000000
                            },
                            'datefield_max': {
                                'value': 1500000000000
                            },
                            'field2_min': {
                                'value': 'A'
                            },
                            'field2_max': {
                                'value': 'Z'
                            }
                        },
                        {
                            'key': {
                                'field1': '1112'
                            },
                            'doc_count': 18,
                            'datefield_min': {
                                'value': None
                            },
                            'datefield_max': {
                                'value': None
                            },
                            'field2_min': {
                                'value': None
                            },
                            'field2_max': {
                                'value': None
                            }
                        }
                    ]
                }
            }
        }

        second_ret = {
            'aggregations': {
                'counts': {
                    'buckets': []
                }
            }
        }

        eds.es.search.side_effect = [
            first_ret,
            second_ret
        ]

        returned = eds.get_group_stats(
            'obj_type',
            group_by='field1',
            stats_fields=['field2', 'datefield'],
            stats=['min', 'max']
        )
        first = next(returned)
        self.assertEqual({
            'key': {'field1': '1111'},
            'stats': {
                'count': 20,
                'datefield': {
                    'min': datetime.fromtimestamp(1000000000),
                    'max': datetime.fromtimestamp(1500000000)
                },
                'field2': {
                    'min': 'A',
                    'max': 'Z'
                }
            }
        }, first)
        second = next(returned)
        self.assertEqual({
            'key': {'field1': '1112'},
            'stats': {
                'count': 18,
                'datefield': {
                    'min': None,
                    'max': None
                },
                'field2': {
                    'min': None,
                    'max': None
                }
            }
        }, second)
        with self.assertRaises(StopIteration):
            next(returned)
        self.assertEqual(eds.es.search.call_count, 2)

    def test_get_group_stats_union(self):
        _, eds = mock_elastic_data_source()

        first_ret = {
            'aggregations': {
                'counts': {
                    'after_key': {
                        'field1': '1234'
                    },
                    'buckets': [
                        {
                            'key': {
                                'field1': '1111'
                            },
                            'doc_count': 20,
                            'field4_union': {
                                'value': ['val1', 'val2', 'val3']
                            }
                        },
                        {
                            'key': {
                                'field1': '1112'
                            },
                            'doc_count': 18,
                            'field4_union': {
                                'value': None
                            }
                        }
                    ]
                }
            }
        }

        second_ret = {
            'aggregations': {
                'counts': {
                    'buckets': []
                }
            }
        }

        eds.es.search.side_effect = [
            first_ret,
            second_ret
        ]

        returned = eds.get_group_stats(
            'obj_type',
            group_by='field1',
            stats_fields=['field4'],
            stats=['union']
        )
        first = next(returned)
        self.assertEqual({
            'key': {'field1': '1111'},
            'stats': {
                'count': 20,
                'field4': {'union': ['val1', 'val2', 'val3']}
            }
        }, first)
        second = next(returned)
        self.assertEqual({
            'key': {'field1': '1112'},
            'stats': {
                'count': 18,
                'field4': {'union': None}
            }
        }, second)
        with self.assertRaises(StopIteration):
            next(returned)
        self.assertEqual(eds.es.search.call_count, 2)

    def test_get_supported_types(self):
        _, eds = mock_elastic_data_source()

        expected = ['index_1', 'index_2']
        eds.es.indices.get_alias.return_value = {
            'test-index-1': {'aliases': {}},
            'test-index-2': {'aliases': {}}
        }

        returned = eds.supported_types
        eds.es.indices.get_alias.assert_called_once()
        self.assertEqual(expected, returned)

        # Test it doesn't call to Elastic the next time
        returned = eds.supported_types
        eds.es.indices.get_alias.assert_called_once()
        self.assertEqual(expected, returned)

    def test_get_attribute_types(self):
        _, eds = mock_elastic_data_source()

        eds.es.indices.get_alias.return_value = {
            'test-index-name': {'aliases': {}}
        }
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
                        },
                        'field_4': {
                            'type': 'boolean'
                        }
                    }
                }
            }
        }
        expected = {'field_1': 'str',
                    'field_2': 'datetime',
                    'field_3': 'int',
                    'field_4': 'bool'}
        returned = eds._get_attribute_types_for_object_type('index_name')
        eds.es.indices.get_mapping.assert_called_once()
        self.assertEqual(expected, returned)

    def test_get_to_one_relationships(self):
        _, eds = mock_elastic_data_source()
        rc = RelationshipConfig()
        rc.to_one = {'relname': 'reltype'}
        eds._relationship_cfg = {'obj_type': rc}
        eds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1',
                            'relname': {'id': '5678',
                                        'field3': 'value3',
                                        'field4': 'value4'}}
            }
        ]
        eds.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'test-reltype': {'aliases': {}}
        }
        source_objects = eds.get_by_id('obj_type', ['1234'])
        source_object = next(source_objects)

        related_object = source_object.to_one_relationships['relname']
        eds.es.indices.get_alias.assert_called_once()
        self.assertEqual(related_object.id, '5678')
        self.assertEqual(related_object.field3, 'value3')

        # More than one returned (shouldn't happen)
        eds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {
                    'field1': 'value1',
                    'relname': [{
                        'id': '5678',
                        'field3': 'value3',
                        'field4': 'value4'
                    }, {
                        'id': '6789',
                        'field3': 'value5',
                        'field4': 'value6'
                    }]
                }
            }
        ]

        source_objects = eds.get_by_id('obj_type', ['1234'])
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        self.assertIsNone(related_object)

        # None returned
        eds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1',
                            'relname': None}
            }
        ]
        source_objects = eds.get_by_id('obj_type', ['1234'])
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        self.assertIsNone(related_object)

        # Relationship name missing
        eds.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1'}
            }
        ]
        source_objects = eds.get_by_id('obj_type', ['1234'])
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        self.assertIsNone(related_object)

    def test_get_to_many_relationships_lazy(self):
        core_data_object, eds = mock_lazy_elastic_data_source()
        rc1 = RelationshipConfig()
        rc1.to_many = {'relname': 'reltype'}
        rc1.foreign_keys = {'relname': 'relfk.id'}
        rc2 = RelationshipConfig()
        rc2.to_one = {'relfk': 'obj_type'}
        eds._relationship_cfg = {'obj_type': rc1, 'reltype': rc2}
        source_object = core_data_object(
            'obj_type',
            {'id': '1'}
        )
        eds.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'test-reltype': {'aliases': {}}
        }
        eds.helpers.scan.return_value = [
            {'_source': {'field3': 'value1',
                         'field4': 'value2',
                         'relfk': {'id': '1'}},
             '_id': '1', '_index': 'hidden-reltype'},
            {'_source': {'field3': 'value3',
                         'field4': 'value4',
                         'relfk': {'id': '1'}},
             '_id': '2', '_index': 'hidden-reltype'}
        ]

        related_objects = source_object.to_many_relationships['relname']
        eds.es.indices.get_alias.assert_called_once()
        eds.helpers.scan.assert_called_once()
        first = next(related_objects)
        self.assertEqual({'field3': 'value1', 'field4': 'value2'}, first.attributes)
        self.assertEqual('1', first.id)
        self.assertEqual('reltype', first.type)
        second = next(related_objects)
        self.assertEqual({'field3': 'value3', 'field4': 'value4'}, second.attributes)
        self.assertEqual('2', second.id)
        self.assertEqual('reltype', second.type)
        with self.assertRaises(StopIteration):
            next(related_objects)

    def test_lazy_get_to_one_relation(self):
        """
        In lazy mode, `ElasticDataSource().get_to_one_relation()` looks in
        `DataObject()._to_one_objects` and either:

        - key is present -> return the object in there
        - key is absent -> fetch the source object, and get it from there
        """

        mock_ds = mock.create_autospec(ElasticDataSource, spec_set=True)
        mock_ds.get_by_id.return_value = None
        type(mock_ds).relationship_config = mock.PropertyMock(
            return_value={
                'a': RelationshipConfig(
                    to_one={'lol': 'b'}
                )
            }
        )
        type(mock_ds).lazy_fetch = mock.PropertyMock(return_value=True)

        # key is present
        expected = mock.Mock()
        mock_obj = mock.create_autospec(DataObject, spec_set=True)
        type(mock_obj).type = mock.PropertyMock(return_value='a')
        type(mock_obj)._to_one_objects = {'lol': expected}
        mock_obj.id = 'hype train'
        observed = ElasticDataSource.get_to_one_relation(mock_ds, mock_obj, 'lol')
        mock_ds.get_one.assert_not_called()
        assert observed == expected

        # key is absent
        expected = mock.Mock()
        # reset `mock_obj._to_one_objects`
        mock_obj._to_one_objects = {}
        mock_inter = mock.create_autospec(DataObject, spec_set=True)
        mock_inter._to_one_objects = {'lol': expected}
        mock_ds.get_one.return_value = mock_inter
        observed = ElasticDataSource.get_to_one_relation(mock_ds, mock_obj, 'lol')
        mock_ds.get_one.assert_called_once_with('a', 'hype train')
        assert observed == expected

    def test_eager_get_to_one_relation(self):
        """
        In eager mode, `ElasticDataSource().get_to_one_relation()` always
        fetches relation objects directly. Uses `._to_one_objects` only to find
        the `target_id`.
        """

        mock_ds = mock.create_autospec(ElasticDataSource, spec_set=True)
        mock_ds.relationship_config = {
            'a': RelationshipConfig(
                to_one={'lol': 'b'}
            )
        }
        mock_ds.lazy_fetch = False

        mock_inter = mock.create_autospec(DataObject, spec_set=True)
        mock_inter2 = mock.create_autospec(DataObject, spec_set=True)
        mock_inter2.id = 'yo'
        mock_inter2.type = 'b'
        mock_inter._to_one_objects = {
            'lol': mock_inter2
        }

        def __side_effect_one(type_: str, __id: str) -> DataObject:
            return mock_inter if type_ == 'a' else mock_inter2

        mock_ds.get_one.side_effect = __side_effect_one

        mock_obj = mock.create_autospec(DataObject, spec_set=True)
        mock_obj.type = 'a'
        mock_obj.id = 'hype train'
        observed = ElasticDataSource.get_to_one_relation(mock_ds, mock_obj, 'lol')
        assert mock_ds.get_one.call_args_list == [
            mock.call('a', 'hype train'),
            mock.call('b', 'yo')
        ]
        assert observed == mock_inter2

    def test_get_enriching_fields(self):
        _, eds = mock_elastic_data_source()

        expected = {'obj_type': ['field1', 'field2']}

        self.assertEqual(expected, eds.enriching_fields)

    def test_relationships_to_enrich(self):
        _, eds = mock_elastic_data_source()

        expected = {
            'reltype': {'obj_type': ['relationship']},
            'obj_type': {'reltype': ['parent']}
        }
        self.assertEqual(expected, eds.relationships_to_enrich)

    def test_get_enrich_update(self):
        _, eds = mock_elastic_data_source()

        expected = [
            (None, {'parent': {'id': 'id1', 'field1': 'value1', 'field2': 'value2'},
                    'parent.id': 'id1'}),
            (None, {'parent': {'id': 'id2', 'field1': 'value3', 'field2': 'value4'},
                    'parent.id': 'id2'})
        ]

        enriching_fields = ['field1', 'field2']
        source_data = [
            eds.data_object_factory(
                'obj_type',
                'id1',
                attributes={'field1': 'value1', 'field2': 'value2'}
            ), eds.data_object_factory(
                'obj_type',
                'id2',
                attributes={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        returned = eds.get_enrich_update(enriching_fields, source_data, 'reltype')
        self.assertEqual(expected, list(returned))

    def test_enrich(self):
        _, eds = mock_elastic_data_source()

        source_data = [
            eds.data_object_factory(
                'obj_type',
                'id1',
                attributes={'field1': 'value1', 'field2': 'value2'}
            ), eds.data_object_factory(
                'obj_type',
                'id2',
                attributes={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        eds.es.update_by_query.return_value = (2, 0)
        eds.enrich('obj_type', source_data, 'reltype')
        self.assertEqual(eds.es.update_by_query.call_count, 2)
