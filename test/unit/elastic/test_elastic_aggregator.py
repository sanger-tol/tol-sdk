# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

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
        actual_result = mock_elastic_data_source._get_date_aggregation(
            'obj_type',
            None,
            'datefield',
            '1M',
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()

    def test_date_aggregation_segmented(self, mock_elastic_data_source: ElasticDataSource):
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'date-aggregation': {
                    'buckets': [
                        {
                            'key': 'DTOL',
                            'document_count': 8767,
                            '1': {
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
                            'document_count': 1909,
                            '1': {
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
        actual_result = mock_elastic_data_source._get_date_aggregation_segmented(
            'obj_type',
            None,
            'datefield',
            '1M',
            'field3',
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()

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
                            "doc_count": 2434,
                            "key": "-"
                        },
                        {
                            "doc_count": 145,
                            "key": "CURATED"
                        },
                        {
                            "doc_count": 192,
                            "key": "DRAFT"
                        },
                        {
                            "doc_count": 912,
                            "key": "IN PROGRESS"
                        },
                        {
                            "doc_count": 2727,
                            "key": "RELEASED"
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
