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
                    'type': 'A',
                    'id': '92',
                    'relationships': {
                        'B': {
                            'links': {
                                'related': '/A/92/B'
                            }
                        }
                    }
                },
                {
                    'type': 'A',
                    'id': '93',
                    'relationships': {
                        'B': {
                            'links': {
                                'related': '/A/93/B'
                            }
                        }
                    }
                }
            ]
        }
        response = self.client.open(
            '/api/v1/A?page=2&page_size=2',
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
                    'type': 'B',
                    'id': '32',
                    'relationships': {
                        'A': {
                            'links': {
                                'related': '/A/233'
                            },
                            'data': {
                                'type': 'A', 'id': '233'
                            }
                        },
                        'E': {
                            'links': {
                                'related': '/B/32/E'
                            }
                        }
                    }
                }
            ]
        }
        response = self.client.open(
            '/api/v1/A/233/B?page=2&page_size=2',
            method='GET',
        )
        print(response.json)
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(expected, response.json)
