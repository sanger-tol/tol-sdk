# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestBadSortByParameter200(BaseTestCase):
    def test_no_sort_by_key_200(self):
        self.add_d(id=890, non_nullable_column='a nice test')
        response = self.client.open(
            '/api/v1/d?sort_by=',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 1)

    def test_sort_by_default_id_ascending_200(self):
        self.add_c(id=89)
        self.add_c(id=39489)
        self.add_c(id=768)
        self.add_c(id=78)

        # no sort_by parameter specified
        response = self.client.open(
            '/api/v1/c',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 4)

        # in correct (ascending) order of id
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 4,
                    'types': {
                        'id': 'int',
                        'nullable_column': 'str',
                        'other_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'c',
                        'id': '78',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': None
                        }
                    },
                    {
                        'type': 'c',
                        'id': '89',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': None
                        }
                    },
                    {
                        'type': 'c',
                        'id': '768',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': None
                        }
                    },
                    {
                        'type': 'c',
                        'id': '39489',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': None
                        }
                    },
                ]
            }
        )

    def test_sort_by_and_filter_200(self):
        self.add_g(id=90909, bool_column=True)
        self.add_g(id=45878, bool_column=False)
        self.add_g(id=7482, bool_column=True)

        # filter for two, sort by id descending
        response = self.client.open(
            '/api/v1/g?sort_by=-id&filter={"exact":{"bool_column":true}}',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 2)

        # assert the two matches are in order, by descending id
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 2,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'datetime_column': 'datetime',
                        'bool_column': 'bool',
                        'string_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'g',
                        'id': '90909',
                        'attributes': {
                            'float_column': None,
                            'datetime_column': None,
                            'bool_column': True,
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '7482',
                        'attributes': {
                            'float_column': None,
                            'datetime_column': None,
                            'bool_column': True,
                            'string_column': None
                        }
                    }
                ]
            }
        )
