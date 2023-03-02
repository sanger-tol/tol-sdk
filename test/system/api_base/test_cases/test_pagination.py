# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestPagination(BaseTestCase):
    # the majority of pagination is implicitly tested elsewhere too
    def test_pagination(self):
        self.add_a(id=90)
        self.add_a(id=91)
        self.add_a(id=92)
        self.add_a(id=93)
        self.add_a(id=94)
        expected = {
            'meta': {
                'page': 2,
                'page_size': 2,
                'offset': 2,
                'limit': 4,
                'total': 5
            },
            'data': [
                {
                    'type': 'a',
                    'id': '92',
                    'attributes': {
                        'string_column': None
                    },
                    'relationships': {
                        'b': {
                            'links': {
                                'related': '/a/92/b'
                            }
                        }
                    }
                },
                {
                    'type': 'a',
                    'id': '93',
                    'attributes': {
                        'string_column': None
                    },
                    'relationships': {
                        'b': {
                            'links': {
                                'related': '/a/93/b'
                            }
                        }
                    }
                }
            ]
        }
        response = self.client.open(
            '/api/v1/a?page=2&page_size=2',
            method='GET',
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(expected, response.json)

    def test_pagination_on_relationship(self):
        self.add_a(id=233)
        self.add_b(id=30, a_id=233)
        self.add_b(id=31, a_id=233)
        self.add_b(id=32, a_id=233)
        expected = {
            'meta': {
                'page': 2,
                'page_size': 2,
                'offset': 2,
                'limit': 4,
                'total': 3
            },
            'data': [
                {
                    'type': 'b',
                    'id': '32',
                    'relationships': {
                        'a': {
                            'links': {
                                'related': '/a/233'
                            },
                            'data': {
                                'type': 'a', 'id': '233'
                            }
                        },
                        'e': {
                            'links': {
                                'related': '/b/32/e'
                            }
                        }
                    }
                }
            ]
        }
        response = self.client.open(
            '/api/v1/a/233/b?page=2&page_size=2',
            method='GET',
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(expected, response.json)
