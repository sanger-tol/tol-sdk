# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestListGetEnum(BaseTestCase):
    def test_filter_bad_enum_name_i_on_list_get_i_400(self):
        # add an I and a connected J
        self.add_i(id=348989, name='right')
        self.add_j(id=34789, I='right')

        # try to filter by a bad name
        response = self.client.open(
            '/api/v1/J?filter=[I=="WRONG"]',
            method='GET'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert it failed for the right reason
        self.assertEqual(
            response.json,
            {
                'errors': [{
                    'title': 'Bad Request',
                    'detail': "The (filter) name 'WRONG' does not "
                              'exist on the enum I.'
                }]
            }
        )

    def test_filter_enum_i_on_list_get_j(self):
        # add three I's
        self.add_i(id=4857, name='easy')
        self.add_i(id=2384, name='as')
        self.add_i(id=93848, name='ABC')

        # add four J's
        self.add_j(id=3847384, I='ABC')
        self.add_j(id=2348, I='easy')
        self.add_j(id=234856, I='ABC')
        self.add_j(id=33, I='as')

        # get I=ABC with id descending
        response = self.client.open(
            '/api/v1/J?filter=[I=="ABC"]&sort_by=-id',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert the correct 2 results were found
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 2
                },
                'data': [
                    {
                        'type': 'J',
                        'id': '3847384',
                        'attributes': {
                            'I': 'ABC'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '234856',
                        'attributes': {
                            'I': 'ABC'
                        }
                    }
                ]
            }
        )

    def test_sort_by_enum_i_on_list_get_j(self):
        # add two I's
        self.add_i(id=4857, name='fun')
        self.add_i(id=2384, name='also fun')

        # add two and three J's respectively
        self.add_j(id=29348, I='fun')
        self.add_j(id=4857, I='also fun')
        self.add_j(id=587, I='fun')
        self.add_j(id=23487, I='also fun')
        self.add_j(id=8394789, I='also fun')

        # sort by I ascending
        response = self.client.open(
            '/api/v1/J?sort_by=I',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that they're in the correct order
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 5
                },
                'data': [
                    {
                        'type': 'J',
                        'id': '4857',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '23487',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '8394789',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '29348',
                        'attributes': {
                            'I': 'fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '587',
                        'attributes': {
                            'I': 'fun'
                        }
                    },
                ]
            }
        )

        # sort by I descending
        response = self.client.open(
            '/api/v1/J?sort_by=-I',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that they're in the correct order
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 5
                },
                'data': [
                    {
                        'type': 'J',
                        'id': '29348',
                        'attributes': {
                            'I': 'fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '587',
                        'attributes': {
                            'I': 'fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '4857',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '23487',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                    {
                        'type': 'J',
                        'id': '8394789',
                        'attributes': {
                            'I': 'also fun'
                        }
                    },
                ]
            }
        )
