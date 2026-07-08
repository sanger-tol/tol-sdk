# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import cast
from unittest import mock

from tol.core import (
    DataObject,
    DataSourceError,
    DataSourceFilter,
)
from tol.core.relationship import RelationshipConfig
from tol.core.requested_fields import ReqFieldsTree
from tol.elastic import (
    ElasticDataSource,
    ElasticUpdateInputConverter,
    ElasticUpdateInputResource,
    ElasticUpsertInputConverter,
    ElasticUpsertInputResource,
)
from tol.elastic.parser import DefaultElasticUpdateInputParser, DefaultElasticUpsertInputParser


dt = datetime.fromtimestamp(1234567890)


class TestUidSubstitution:
    """
    `uid` is a private attribute, put in place as a
    workaround of the limitations of ElasticSearch,
    regarding document `id` fields.

    `ElasticDataSource` must internally use `uid`, but
    expose this as `id` proper.
    """

    def test_sort_by_id_asc(self, mock_elastic_data_source: ElasticDataSource):
        """
        `ElasticDataSource().get_list_page()` converts
        sort_by directives containing `id` to `uid`
        internally.
        """
        self.__test_uid_sort('id', 'asc', mock_elastic_data_source)

    def test_sort_by_id_desc(self, mock_elastic_data_source: ElasticDataSource):
        """
        `ElasticDataSource().get_list_page()` converts
        sort_by directives containing `id` to `uid`
        internally.
        """
        self.__test_uid_sort('-id', 'desc', mock_elastic_data_source)

    def test_get_by_id(self, mock_elastic_data_source: ElasticDataSource):
        """
        `ElasticDataSource().get_by_id()` removes `uid`
        from elastic transfers
        """
        mock_elastic_data_source.helpers.scan.return_value = [
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
            mock_elastic_data_source.get_by_id('obj_type', ['lol'])
        )

        assert 'uid' not in obj.attributes

    def __test_uid_sort(
        self, sort_by: str, order: str, mock_elastic_data_source: ElasticDataSource
    ) -> None:

        expected_sort = [
            {
                'uid.keyword': {
                    'order': order,
                    'unmapped_type': 'keyword'
                }
            }
        ]

        mock_elastic_data_source.es.search.return_value = {
            'hits': {
                'hits': [],
                'total': {'value': 0}
            }
        }

        mock_elastic_data_source.get_list_page(
            'obj_type',
            1,
            sort_by=sort_by
        )

        mock_elastic_data_source.es.search.assert_called_once()

        (_, kwargs) = mock_elastic_data_source.es.search.call_args_list[0]
        assert kwargs['sort'] == expected_sort


class TestElasticDataSource:

    def test_requested_tree_filtering(self, mock_elastic_data_source: ElasticDataSource):
        # Test no requested tree
        f = DataSourceFilter()
        f.and_ = {
            'field7': {'eq': {'value': 'test'}},
            'field8': {'eq': {'value': '2020-01-01', 'negate': True}}
        }
        (
            real_index_name,
            query,
            fields,
            runtime_mappings
        ) = mock_elastic_data_source._prepare_get_parameters(
            object_type='obj_type',
            object_filters=f,
        )
        assert real_index_name == 'test-obj-type'
        assert query == {
            'bool': {
                'must': [
                    {'match': {'field7': 'test'}},
                ],
                'must_not': [
                    {'match': {'field8': datetime(2020, 1, 1, 0, 0)}},
                ]
            }
        }
        assert fields == ['field7', 'field8', 'field5.value','relationship.id.value']
        assert list(cast(dict, runtime_mappings).keys()) == [
            'field7', 'field8', 'field5.value', 'relationship.id.value'
        ]

        # Test with requested tree.
        # Both fields and mappings should have filters
        f = DataSourceFilter()
        f.and_ = {
            'field7': {'eq': {'value': 'test'}},
        }
        requested_tree = ReqFieldsTree('obj_type', mock_elastic_data_source, ['field8'])
        (
            real_index_name,
            query,
            fields,
            runtime_mappings
        ) = mock_elastic_data_source._prepare_get_parameters(
            object_type='obj_type',
            object_filters=f,
            requested_tree=requested_tree,
        )
        assert real_index_name == 'test-obj-type'
        assert query == {
            'bool': {
                'must': [
                    {'match': {'field7': 'test'}},
                ],
                'must_not': []
            }
        }
        assert fields == ['field7', 'field8']
        assert list(cast(dict, runtime_mappings).keys()) == ['field7', 'field8']

        # Test with requested relation subtree.
        # relation runtime fields must be retained for provenanced relation ids.
        requested_tree = ReqFieldsTree(
            'obj_type',
            mock_elastic_data_source,
            ['relationship.field3']
        )
        (
            _,
            _,
            fields,
            runtime_mappings
        ) = mock_elastic_data_source._prepare_get_parameters(
            object_type='obj_type',
            object_filters=None,
            requested_tree=requested_tree,
        )
        assert fields == ['relationship.id.value']
        assert list(cast(dict, runtime_mappings).keys()) == ['relationship.id.value']

    def test_upsert(self, mock_elastic_data_source: ElasticDataSource):
        CoreDataObject = mock_elastic_data_source.data_object_factory  # noqa N806

        objects = [
            CoreDataObject(
                'obj_type',
                id_='1',
                attributes={
                    'field1': 'value1',
                    'field2': 'value2',
                    'field5': 'value5',  # provenanced
                    'datefield': dt
                },
                to_one={
                    'relationship': CoreDataObject(
                        'reltype',
                        id_='rel1'
                    ),
                    'another_relationship': CoreDataObject(
                        'reltype',
                        id_='rel2'
                    )

                }
            ),
            CoreDataObject(
                'obj_type',
                id_='2',
                attributes={
                    'field1': 'value3',
                    'field2': 'value4'
                }
            )
        ]
        converter = ElasticUpsertInputConverter(
            DefaultElasticUpsertInputParser(mock_elastic_data_source)
        )
        generator = converter.convert(ElasticUpsertInputResource(
            'test-obj-type',
            objects,
            id_func=lambda x: x.id,
            provenance='source_1'
        ))
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': '1',
            'script': {
                'source': DefaultElasticUpsertInputParser(mock_elastic_data_source)._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field1': 'value1',
                        'field2': 'value2',
                        'field5': {
                            'provenance': {
                                'source_1': {
                                    'value': 'value5'
                                }
                            }
                        },
                        'datefield': dt.isoformat(),
                        'relationship': {
                            'id': {
                                'provenance': {
                                    'source_1': {
                                        'value': 'rel1'
                                    }
                                }
                            }
                        },
                        'another_relationship': {
                            'id': 'rel2'
                        },
                        'uid': '1'
                    }
                }
            }
        }
        assert next(generator) == expected
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': '2',
            'script': {
                'source': DefaultElasticUpsertInputParser(mock_elastic_data_source)._upsert_script,
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
        assert next(generator) == expected
        mock_elastic_data_source.helpers.bulk.return_value = (2, 0)
        mock_elastic_data_source.upsert('index', objects, id_func=lambda x: x.field1)
        mock_elastic_data_source.helpers.bulk.assert_called_once()

    def test_upsert_add_id(self, mock_elastic_data_source: ElasticDataSource):
        CoreDataObject = mock_elastic_data_source.data_object_factory  # noqa N806

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
        converter = ElasticUpsertInputConverter(
            DefaultElasticUpsertInputParser(mock_elastic_data_source)
        )
        generator = converter.convert(ElasticUpsertInputResource(
            'test-obj-type',
            objects,
            id_func=lambda x: x.field1
        ))
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 'value1',
            'script': {
                'source': DefaultElasticUpsertInputParser(mock_elastic_data_source)._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field1': 'value1',
                        'field2': 'value2',
                        'uid': 'value1'
                    }
                }
            }
        }
        assert next(generator) == expected
        expected = {
            '_op_type': 'update',
            'scripted_upsert': True,
            'upsert': {},
            '_index': 'test-obj-type',
            '_id': 'value3',
            'script': {
                'source': DefaultElasticUpsertInputParser(mock_elastic_data_source)._upsert_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field1': 'value3',
                        'field2': 'value4',
                        'uid': 'value3'
                    }
                }
            }
        }
        assert next(generator) == expected
        mock_elastic_data_source.helpers.bulk.return_value = (2, 0)
        mock_elastic_data_source.upsert('index', objects, id_func=lambda x: x.field1)
        mock_elastic_data_source.helpers.bulk.assert_called_once()

    def test_upsert_error(self, mock_elastic_data_source: ElasticDataSource):
        objects = [{'field1': 'value1', 'field2': 'value2'},
                   {'field1': 'value3', 'field2': 'value4'}]
        mock_elastic_data_source.helpers.bulk.return_value = (2, 1)
        try:
            mock_elastic_data_source.upsert('object_type', objects, id_func=lambda x: x.field1)
        except DataSourceError:
            pass
        else:
            assert False, 'Expected DataSourceError to be raised'

    def test_update(self, mock_elastic_data_source: ElasticDataSource):
        CoreDataObject = mock_elastic_data_source.data_object_factory  # noqa N806

        update1 = {
            'field1': 'value1',
            'field2': 'value2',
            'field5': 'value5',  # provenanced
            'relationship': CoreDataObject(
                'reltype',
                id_='rel1',
                attributes={'field3': 'string1', 'field4': 'string2'}
            ),
            'another_relationship': CoreDataObject(
                'reltype',
                id_='rel2',
                attributes={'field3': 'string1', 'field4': 'string2'}
            )
        }

        update2 = {'field1': 'value3',
                   'field2': 'value4'}
        updates = [(None, update1),
                   (None, update2)]

        converter = ElasticUpdateInputConverter(
            DefaultElasticUpdateInputParser(mock_elastic_data_source)
        )
        update_body = converter.convert(ElasticUpdateInputResource(
            'obj_type',
            update1,
            candidate_key=['field1'],
            provenance='source_1'
        ))
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
                'source': DefaultElasticUpdateInputParser(mock_elastic_data_source)._update_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': {
                        'field2': 'value2',
                        'field5': {
                            'provenance': {
                                'source_1': {
                                    'value': 'value5'
                                }
                            },
                        },
                        'relationship': {
                            'id': {'provenance': {'source_1': {'value': 'rel1'}}},
                            'field3': 'string1',
                            'field4': 'string2'
                        },
                        'another_relationship': {
                            'id': 'rel2',
                            'field3': 'string1',
                            'field4': 'string2'
                        }
                    }
                }
            }
        }
        assert update_body == expected
        mock_elastic_data_source.es.update_by_query.return_value = (2, 0)
        mock_elastic_data_source.update('obj_type', updates, candidate_key=['field1'])
        assert mock_elastic_data_source.es.update_by_query.call_count == 2

    def test_get_list(self, mock_elastic_data_source: ElasticDataSource):
        mock_elastic_data_source.helpers.scan.return_value = [
            {'_source': {'field1': 'value1', 'field2': 'value2'},
             'fields': {'field7': ['Hello']},
             '_id': '1', '_index': 'test-obj-type'},
            {'_source': {'field1': 'value3', 'field2': 'value4'},
             'fields': {'field7': ['Hello']},
             '_id': '2', '_index': 'test-obj-type'}
        ]

        returned = iter(mock_elastic_data_source.get_list('obj_type'))
        mock_elastic_data_source.helpers.scan.assert_called_once()
        first = next(returned)
        assert first.attributes == {'field1': 'value1', 'field2': 'value2', 'field7': 'Hello'}
        assert first.id == '1'
        assert first.type == 'obj_type'
        second = next(returned)
        assert second.attributes == {'field1': 'value3', 'field2': 'value4', 'field7': 'Hello'}
        assert second.id == '2'
        assert second.type == 'obj_type'
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be raised'

    def test_get_list_page(self, mock_elastic_data_source: ElasticDataSource):
        mock_elastic_data_source.es.search.return_value = {
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

        returned, total = mock_elastic_data_source.get_list_page('obj_type', 3)
        returned = iter(returned)
        mock_elastic_data_source.es.search.assert_called_once()
        assert total == 2
        first = next(returned)
        assert first.attributes == {'field1': 'value1', 'field2': 'value2', 'field7': 'Hello'}
        assert first.id == '1'
        assert first.type == 'obj_type'
        second = next(returned)
        assert second.attributes == {'field1': 'value3', 'field2': 'value4', 'field7': 'Hello'}
        assert second.id == '2'
        assert second.type == 'obj_type'
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be raised'

    def test_get_by_id(self, mock_elastic_data_source: ElasticDataSource):
        mock_elastic_data_source.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1',
                '_source': {
                    'field1': 'value1',
                    'field2': 'value2',
                    'field5': {'provenance': {'source_1': {'value': 'value5'}}},
                    'relationship': {
                        'id': {'provenance': {'source_1': {'value': 'rel1'}}}
                    },
                    'another_relationship': {
                        'id': 'rel2'
                    },
                },
                'fields': {
                    'field7': ['Hello'],
                    'field5.value': ['value5'],
                    'relationship.id.value': ['rel1']
                },
            },
            {
                '_index': 'test-obj-type',
                '_id': '2',
                '_source': {'field1': 'value3', 'field2': 'value4'},
                'fields': {'field7': ['Hello']},
            }
        ]

        returned = iter(mock_elastic_data_source.get_by_id('obj_type', ['2', '1']))
        first = next(returned)
        print(first.attributes)
        assert first.attributes == {
            'field1': 'value3',
            'field2': 'value4',
            'field7': 'Hello'
        }
        assert first.id == '2'
        assert first.type == 'obj_type'
        second = next(returned)
        assert second.attributes == {
            'field1': 'value1',
            'field2': 'value2',
            'field5': 'value5',
            'field7': 'Hello'
        }
        assert second.id == '1'
        assert second.type == 'obj_type'
        assert second.relationship.id == 'rel1'
        assert second.another_relationship.id == 'rel2'
        assert second.provenance['field5']['source_1'] == 'value5'
        assert second.provenance['relationship']['source_1'].id == 'rel1'
        assert 'field1' not in second.provenance
        assert 'another_relationship' not in second.provenance
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be raised'
        mock_elastic_data_source.helpers.scan.assert_called_once()

    def test_build_sort(self, mock_elastic_data_source: ElasticDataSource):
        expected = [{'uid.keyword': 'asc'}]
        assert mock_elastic_data_source._build_elasticsearch_sort('obj_type', None) == expected

        # Asc
        sort_by = 'field1'
        expected = [{'field1.keyword': 'asc'}, {'uid.keyword': 'asc'}]
        assert mock_elastic_data_source._build_elasticsearch_sort('obj_type', sort_by) == expected

        # Desc
        sort_by = '-field1'
        expected = [{'field1.keyword': 'desc'}, {'uid.keyword': 'asc'}]
        assert mock_elastic_data_source._build_elasticsearch_sort('obj_type', sort_by) == expected

    def test_get_aggregations(self, mock_elastic_data_source: ElasticDataSource):
        """
        Checks that the correct aggregation method is called for the arguments provided
        """
        # Replace the aggregation methods with mocks.
        # We're not testing their functionality here, only which one was called
        # (for functionality, see the tests for ElasticAggregator)
        mock_elastic_data_source._get_date_aggregation = mock.Mock(return_value={})
        mock_elastic_data_source._get_date_aggregation_segmented = mock.Mock(return_value={})
        mock_elastic_data_source._get_categorical_aggregation = mock.Mock(return_value={})
        mock_elastic_data_source._get_categorical_aggregation_segmented = mock.Mock(
            return_value={}
        )
        # TODO: Add scatter ones here when that's done

        # Date aggregation combination
        result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='datefield',
            date_interval='1M',
        )
        assert result == {}
        mock_elastic_data_source._get_date_aggregation.assert_called_once()

        # Date segmented aggregation combination
        result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='datefield',
            date_interval='1M',
            break_down_by='field3',
        )
        assert result == {}
        mock_elastic_data_source._get_date_aggregation_segmented.assert_called_once()

        # TODO Scatter aggregation here

        # Categorical aggregation combination
        result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='field4',
        )
        assert result == {}
        mock_elastic_data_source._get_categorical_aggregation.assert_called_once()

        # Categorical segmented aggregation combination
        result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='field4',
            break_down_by='field3',
        )
        assert result == {}
        mock_elastic_data_source._get_categorical_aggregation_segmented.assert_called_once()

        # Invalid combination
        result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='field3',
            maximum_categories=8,
        )
        assert result is None

    def test_cumulative_aggregation(self, mock_elastic_data_source: ElasticDataSource):
        """
        Check whether the accumulation post-processing step functions correctly.

        This step is separate to the aggregation performed. A date aggregation is used here,
        but it could be any one.
        This test is structured similarly to test_date_aggregation in the ElasticAggregator tests,
        so if that changes this should too
        """
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'date-aggregation': {
                    'buckets': [
                        {
                            'doc_count': 27,
                            'key': 1735689600,
                            'key_as_string': '2025-01-01',
                        },
                        {
                            'doc_count': 30,
                            'key': 1735776000,
                            'key_as_string': '2025-01-02',
                        }
                    ]
                }
            }
        }

        expected_result = [{
            'key': None,
            'data': [
                {
                    'x': '2025-01-01',
                    'y': 27,
                },
                {
                    'x': '2025-01-02',
                    'y': 57,
                },
            ]
        }]
        actual_result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='datefield',
            date_interval='1M',
            cumulative=True,
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()

    def test_get_aggregations_legacy(self, mock_elastic_data_source: ElasticDataSource):
        agg_result = {
            'my-agg-name': {
                'doc_count_error_upper_bound': 0,
                'sum_other_doc_count': 0,
                'buckets': []
            }
        }
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': agg_result
        }

        aggregations = {
            'my-agg-name': {
                'terms': {
                    'field': 'my-field'
                }
            }
        }
        returned = mock_elastic_data_source.get_aggregations_legacy(
            'index',
            aggregations=aggregations
        )
        mock_elastic_data_source.es.search.assert_called_once()
        assert returned == agg_result

    def test_get_count(self, mock_elastic_data_source: ElasticDataSource):
        mock_elastic_data_source.es.search.return_value = {
            'hits': {
                'total': {
                    'value': 12345
                }
            }
        }

        returned = mock_elastic_data_source.get_count('obj_type')
        mock_elastic_data_source.es.search.assert_called_once()
        assert returned == 12345

    def test_get_stats_unique_and_cardinality(self, mock_elastic_data_source: ElasticDataSource):
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
        mock_elastic_data_source.es.search.side_effect = [
            ret
        ]

        returned = mock_elastic_data_source.get_stats(
            'obj_type',
            stats_fields=['field2', 'datefield'],
            stats=['unique', 'cardinality']
        )
        assert returned == {
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
        }
        assert mock_elastic_data_source.es.search.call_count == 1

    def test_get_group_stats_standard(self, mock_elastic_data_source: ElasticDataSource):
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

        mock_elastic_data_source.es.search.side_effect = [
            first_ret,
            second_ret
        ]

        returned = iter(mock_elastic_data_source.get_group_stats(
            'obj_type',
            group_by=['field1'],
            stats_fields=['field2', 'datefield'],
            stats=['min', 'max']
        ))
        first = next(returned)
        assert first == {
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
        }
        second = next(returned)
        assert second == {
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
        }
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be raised'
        assert mock_elastic_data_source.es.search.call_count == 2

    def test_get_group_stats_union(self, mock_elastic_data_source: ElasticDataSource):
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

        mock_elastic_data_source.es.search.side_effect = [
            first_ret,
            second_ret
        ]

        returned = iter(mock_elastic_data_source.get_group_stats(
            'obj_type',
            group_by=['field1'],
            stats_fields=['field4'],
            stats=['union']
        ))
        first = next(returned)
        assert first == {
            'key': {'field1': '1111'},
            'stats': {
                'count': 20,
                'field4': {'union': ['val1', 'val2', 'val3']}
            }
        }
        second = next(returned)
        assert second == {
            'key': {'field1': '1112'},
            'stats': {
                'count': 18,
                'field4': {'union': None}
            }
        }
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be called'
        assert mock_elastic_data_source.es.search.call_count == 2

    def test_get_group_stats_recent(self, mock_elastic_data_source: ElasticDataSource):
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
                            'field4_recent': {
                                'value': 'val1'
                            }
                        },
                        {
                            'key': {
                                'field1': '1112'
                            },
                            'doc_count': 18,
                            'field4_recent': {
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

        mock_elastic_data_source.es.search.side_effect = [
            first_ret,
            second_ret
        ]

        returned = iter(mock_elastic_data_source.get_group_stats(
            'obj_type',
            group_by=['field1'],
            stats_fields=['field4', 'datefield'],
            stats=['recent']
        ))
        first = next(returned)
        assert first == {
            'key': {'field1': '1111'},
            'stats': {
                'count': 20,
                'field4': {'recent': 'val1'}
            }
        }
        second = next(returned)
        assert second == {
            'key': {'field1': '1112'},
            'stats': {
                'count': 18,
                'field4': {'recent': None}
            }
        }
        try:
            next(returned)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be called'
        assert mock_elastic_data_source.es.search.call_count == 2

    def test_get_supported_types(self, mock_elastic_data_source: ElasticDataSource):
        expected = ['index_1', 'index_2']
        mock_elastic_data_source.es.indices.get_alias.return_value = {
            'test-index-1': {'aliases': {}},
            'test-index-2': {'aliases': {}}
        }

        returned = mock_elastic_data_source.supported_types
        mock_elastic_data_source.es.indices.get_alias.assert_called_once()
        assert returned == expected

        # Test it doesn't call to Elastic the next time
        returned = mock_elastic_data_source.supported_types
        mock_elastic_data_source.es.indices.get_alias.assert_called_once()
        assert returned == expected

    def test_get_attribute_types(self, mock_elastic_data_source: ElasticDataSource):
        mock_elastic_data_source.es.indices.get_alias.return_value = {
            'test-index-name': {'aliases': {}}
        }
        mock_elastic_data_source.es.indices.get_mapping.return_value = {
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
        returned = mock_elastic_data_source._get_attribute_types_for_object_type('index_name')
        mock_elastic_data_source.es.indices.get_mapping.assert_called_once()
        assert returned == expected

    def test_get_to_one_relationships(self, mock_elastic_data_source: ElasticDataSource):
        rc = RelationshipConfig()
        rc.to_one = {'relname': 'reltype'}
        mock_elastic_data_source._relationship_cfg = {'obj_type': rc}
        mock_elastic_data_source.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1',
                            'relname': {'id': '5678',
                                        'field3': 'value3',
                                        'field4': 'value4'}}
            }
        ]
        mock_elastic_data_source.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'test-reltype': {'aliases': {}}
        }
        source_objects = iter(mock_elastic_data_source.get_by_id('obj_type', ['1234']))
        source_object = next(source_objects)

        related_object = source_object.to_one_relationships['relname']
        assert related_object is not None
        mock_elastic_data_source.es.indices.get_alias.assert_called_once()
        assert related_object.id == '5678'
        assert related_object.field3 == 'value3'

        # More than one returned (shouldn't happen)
        mock_elastic_data_source.helpers.scan.return_value = [
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

        source_objects = iter(mock_elastic_data_source.get_by_id('obj_type', ['1234']))
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        assert related_object is None

        # None returned
        mock_elastic_data_source.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1',
                            'relname': None}
            }
        ]
        source_objects = iter(mock_elastic_data_source.get_by_id('obj_type', ['1234']))
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        assert related_object is None

        # Relationship name missing
        mock_elastic_data_source.helpers.scan.return_value = [
            {
                '_index': 'test-obj-type',
                '_id': '1234',
                '_source': {'field1': 'value1'}
            }
        ]
        source_objects = iter(mock_elastic_data_source.get_by_id('obj_type', ['1234']))
        source_object = next(source_objects)
        related_object = source_object.to_one_relationships['relname']
        assert related_object is None

    def test_get_to_many_relationships_lazy(
        self, mock_lazy_elastic_data_source: ElasticDataSource
    ):
        CoreDataObject = mock_lazy_elastic_data_source.data_object_factory  # noqa N806

        rc1 = RelationshipConfig()
        rc1.to_many = {'relname': 'reltype'}
        rc1.foreign_keys = {'relname': 'relfk.id'}
        rc2 = RelationshipConfig()
        rc2.to_one = {'relfk': 'obj_type'}
        mock_lazy_elastic_data_source._relationship_cfg = {'obj_type': rc1, 'reltype': rc2}
        source_object = CoreDataObject(
            'obj_type',
            {'id': '1'}
        )
        mock_lazy_elastic_data_source.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'test-reltype': {'aliases': {}}
        }
        mock_lazy_elastic_data_source.helpers.scan.return_value = [
            {'_source': {'field3': 'value1',
                         'field4': 'value2',
                         'relfk': {'id': '1'}},
             '_id': '1', '_index': 'hidden-reltype'},
            {'_source': {'field3': 'value3',
                         'field4': 'value4',
                         'relfk': {'id': '1'}},
             '_id': '2', '_index': 'hidden-reltype'}
        ]

        related_objects = iter(source_object.to_many_relationships['relname'])
        mock_lazy_elastic_data_source.es.indices.get_alias.assert_called_once()
        mock_lazy_elastic_data_source.helpers.scan.assert_called_once()
        first = next(related_objects)
        assert first.attributes == {'field3': 'value1', 'field4': 'value2'}
        assert first.id == '1'
        assert first.type == 'reltype'
        second = next(related_objects)
        assert second.attributes == {'field3': 'value3', 'field4': 'value4'}
        assert second.id == '2'
        assert second.type == 'reltype'
        try:
            next(related_objects)
        except StopIteration:
            pass
        else:
            assert False, 'Expected StopIteration to be raised'

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

    def test_get_enriching_fields(self, mock_elastic_data_source: ElasticDataSource):
        expected = {'obj_type': ['field1', 'field2']}
        assert mock_elastic_data_source.enriching_fields == expected

    def test_relationships_to_enrich(self, mock_elastic_data_source: ElasticDataSource):
        expected = {
            'reltype': {'obj_type': ['relationship', 'another_relationship']},
            'obj_type': {'reltype': ['parent']}
        }
        assert mock_elastic_data_source.relationships_to_enrich == expected

    def test_get_enrich_update(self, mock_elastic_data_source: ElasticDataSource):
        expected = [
            (None, {'parent': {'id': 'id1', 'field1': 'value1', 'field2': 'value2'},
                    'parent.id': 'id1'}),
            (None, {'parent': {'id': 'id2', 'field1': 'value3', 'field2': 'value4'},
                    'parent.id': 'id2'})
        ]

        enriching_fields = ['field1', 'field2']
        source_data = [
            mock_elastic_data_source.data_object_factory(
                'obj_type',
                'id1',
                attributes={'field1': 'value1', 'field2': 'value2'}
            ), mock_elastic_data_source.data_object_factory(
                'obj_type',
                'id2',
                attributes={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        returned = mock_elastic_data_source.get_enrich_update(
            enriching_fields, source_data, 'reltype'
        )
        assert list(returned) == expected

    def test_enrich(self, mock_elastic_data_source: ElasticDataSource):
        source_data = [
            mock_elastic_data_source.data_object_factory(
                'obj_type',
                'id1',
                attributes={'field1': 'value1', 'field2': 'value2'}
            ), mock_elastic_data_source.data_object_factory(
                'obj_type',
                'id2',
                attributes={'field1': 'value3', 'field2': 'value4'}
            )
        ]
        mock_elastic_data_source.es.update_by_query.return_value = (2, 0)
        mock_elastic_data_source.enrich('obj_type', source_data, 'reltype')
        assert mock_elastic_data_source.es.update_by_query.call_count == 2
