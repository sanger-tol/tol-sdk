# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

from tol.elastic import ElasticDataSource


class TestElasticAggregator:
    def test_date_aggregation(self, mock_elastic_data_source: ElasticDataSource):
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
                    'y': 30,
                },
            ]
        }]
        with mock.patch.object(
            mock_elastic_data_source,
            '_field_or_keyword',
            return_value='datefield.value',
        ) as field_or_keyword:
            actual_result = mock_elastic_data_source._get_date_aggregation(
                'obj_type',
                None,
                'datefield',
                '1M',
            )
        assert actual_result == expected_result
        field_or_keyword.assert_called_once_with('obj_type', 'datefield')
        search_kwargs = mock_elastic_data_source.es.search.call_args.kwargs
        assert search_kwargs['aggregations']['date-aggregation']['date_histogram']['field'] \
            == 'datefield.value'

    def test_date_aggregation_segmented(self, mock_elastic_data_source: ElasticDataSource):
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'break-down-by-aggregation': {
                    'buckets': [
                        {
                            'key': 'DTOL',
                            'document_count': 8767,
                            'date-aggregation': {
                                'doc_count_error_upper_bound': 0,
                                'sum_other_doc_count': 0,
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
                        },
                        {
                            'key': 'PSYCHE',
                            'doc_count': 1909,
                            'date-aggregation': {
                                'doc_count_error_upper_bound': 0,
                                'sum_other_doc_count': 0,
                                'buckets': [
                                    {
                                        'doc_count': 15,
                                        'key': 1735689600,
                                        'key_as_string': '2025-01-01',
                                    },
                                    {
                                        'doc_count': 20,
                                        'key': 1735776000,
                                        'key_as_string': '2025-01-02',
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

        expected_result = [
            {
                'key': 'DTOL',
                'data': [
                    {
                        'x': '2025-01-01',
                        'y': 27,
                    },
                    {
                        'x': '2025-01-02',
                        'y': 30,
                    },
                ]
            },
            {
                'key': 'PSYCHE',
                'data': [
                    {
                        'x': '2025-01-01',
                        'y': 15,
                    },
                    {
                        'x': '2025-01-02',
                        'y': 20,
                    },
                ]
            },
        ]
        with mock.patch.object(
            mock_elastic_data_source,
            '_field_or_keyword',
            side_effect=lambda object_type, field: f'{field}.value',
        ) as field_or_keyword:
            actual_result = mock_elastic_data_source._get_date_aggregation_segmented(
                'obj_type',
                None,
                'datefield',
                '1M',
                'field3',
            )
        assert actual_result == expected_result
        assert field_or_keyword.call_args_list == [
            mock.call('obj_type', 'field3'),
            mock.call('obj_type', 'datefield'),
        ]
        search_kwargs = mock_elastic_data_source.es.search.call_args.kwargs
        aggregations = search_kwargs['aggregations']['break-down-by-aggregation']
        assert aggregations['terms']['field'] == 'field3.value'
        assert aggregations['aggs']['date-aggregation']['date_histogram']['field'] \
            == 'datefield.value'

    def test_scatter_aggregation(self, mock_elastic_data_source: ElasticDataSource):
        # TODO Once the scatter aggregation has been implemented
        pass

    def test_categorical_aggregation(self, mock_elastic_data_source: ElasticDataSource):
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'categorical-aggregation': {
                    'buckets': [
                        {
                            'doc_count': 2434,
                            'key': '-',
                        },
                        {
                            'doc_count': 145,
                            'key': 'CURATED',
                        },
                        {
                            'doc_count': 192,
                            'key': 'DRAFT',
                        },
                        {
                            'doc_count': 912,
                            'key': 'IN PROGRESS',
                        },
                        {
                            'doc_count': 2727,
                            'key': 'RELEASED',
                        },
                    ]
                }
            }
        }

        expected_result = [{
            'key': None,
            'data': [
                {
                    'x': '-',
                    'y': 2434,
                },
                {
                    'x': 'CURATED',
                    'y': 145,
                },
                {
                    'x': 'DRAFT',
                    'y': 192,
                },
                {
                    'x': 'IN PROGRESS',
                    'y': 912,
                },
                {
                    'x': 'RELEASED',
                    'y': 2727,
                },
            ]
        }]
        actual_result = mock_elastic_data_source._get_categorical_aggregation(
            'obj_type',
            None,
            'field4',
            5,  # TODO: Maximum categories
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()

    def test_categorical_aggregation_segmented(self, mock_elastic_data_source: ElasticDataSource):
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'break-down-by-aggregation': {
                    'buckets': [
                        {
                            'key': 'DTOL',
                            'doc_count': 8767,
                            'categorical-aggregation': {
                                'doc_count_error_upper_bound': 0,
                                'sum_other_doc_count': 0,
                                'buckets': [
                                    {
                                        'doc_count': 2434,
                                        'key': '-',
                                    },
                                    {
                                        'doc_count': 145,
                                        'key': 'CURATED',
                                    },
                                    {
                                        'doc_count': 192,
                                        'key': 'DRAFT',
                                    },
                                    {
                                        'doc_count': 912,
                                        'key': 'IN PROGRESS',
                                    },
                                    {
                                        'doc_count': 2727,
                                        'key': 'RELEASED',
                                    },
                                ]
                            }
                        },
                        {
                            'key': 'PSYCHE',
                            'doc_count': 1909,
                            'categorical-aggregation': {
                                'doc_count_error_upper_bound': 0,
                                'sum_other_doc_count': 0,
                                'buckets': [
                                    {
                                        'doc_count': 246,
                                        'key': '-'
                                    },
                                    {
                                        'doc_count': 31,
                                        'key': 'CURATED'
                                    },
                                    {
                                        'doc_count': 5,
                                        'key': 'DRAFT'
                                    },
                                    {
                                        'doc_count': 45,
                                        'key': 'IN PROGRESS'
                                    },
                                    {
                                        'doc_count': 90,
                                        'key': 'RELEASED'
                                    },
                                ]
                            }
                        },
                    ]
                }
            }
        }

        expected_result = [
            {
                'key': 'DTOL',
                'data': [
                    {
                        'x': '-',
                        'y': 2434,
                    },
                    {
                        'x': 'CURATED',
                        'y': 145,
                    },
                    {
                        'x': 'DRAFT',
                        'y': 192,
                    },
                    {
                        'x': 'IN PROGRESS',
                        'y': 912,
                    },
                    {
                        'x': 'RELEASED',
                        'y': 2727,
                    },
                ]
            },
            {
                'key': 'PSYCHE',
                'data': [
                    {
                        'x': '-',
                        'y': 246,
                    },
                    {
                        'x': 'CURATED',
                        'y': 31,
                    },
                    {
                        'x': 'DRAFT',
                        'y': 5,
                    },
                    {
                        'x': 'IN PROGRESS',
                        'y': 45,
                    },
                    {
                        'x': 'RELEASED',
                        'y': 90,
                    },
                ]
            },
        ]
        actual_result = mock_elastic_data_source._get_categorical_aggregation_segmented(
            'obj_type',
            None,
            'field4',
            5,  # TODO: Maximum categories
            'field3',
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()
