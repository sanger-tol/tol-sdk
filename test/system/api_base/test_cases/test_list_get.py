# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestListGet(BaseTestCase):
    def test_get_multiple_inserted_c_200(self):
        c_1 = {
            'id': 9090,
        }
        c_2 = {
            'id': 80808,
            'nullable_column': 'hello, how are you'
        }
        c_3 = {
            'id': 989089,
            'other_column': 'fine, and yourself?'
        }
        self.add_c(**c_1)
        self.add_c(**c_2)
        self.add_c(**c_3)

        response = self.client.open(
            '/api/v1/c',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 3
                },
                'data': [
                    {
                        'type': 'c',
                        'id': '9090',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': None
                        }
                    },
                    {
                        'type': 'c',
                        'id': '80808',
                        'attributes': {
                            'nullable_column': 'hello, how are you',
                            'other_column': None
                        }
                    },
                    {
                        'type': 'c',
                        'id': '989089',
                        'attributes': {
                            'nullable_column': None,
                            'other_column': 'fine, and yourself?'
                        }
                    },
                ]
            }
        )

    def test_paged_correct_quantity_c_200(self):
        for i in range(47):
            self.add_c(
                id=i,
                nullable_column='attack of the clones'
            )

        # (implictly) first page
        response = self.client.open(
            '/api/v1/c',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # should be fully populated
        self.assertEqual(len(response.json['data']), 20)

        # last (partially) populated page
        response = self.client.open(
            '/api/v1/c?page=3',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # 7 = 47 - 20*2
        self.assertEqual(len(response.json['data']), 7)

        # first unpopulated page
        response = self.client.open(
            '/api/v1/c?page=4',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 0)

        # obviously out of range page
        response = self.client.open(
            '/api/v1/c?page=9999',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # should not be populated at all
        self.assertEqual(len(response.json['data']), 0)

    def test_quantity_all_parameters_simultaneously_get_c_200(self):
        # add 50 C's, half of which the filter should match
        for i in range(50):
            self.add_c(
                id=i,
                nullable_column='monoclonal antibodies'
                if i % 2 == 0
                else 'something about clones'
            )

        response = self.client.open(
            '/api/v1/c?page=2&sort_by=-nullable_column&filter='
            '{"exact":{"nullable_column": "something about clones"}}',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # 5 = 50/2 - 20
        self.assertEqual(len(response.json['data']), 5)

    def test_bad_page_get_c_400(self):
        self.add_c(
            id=100,
            nullable_column='test not clone'
        )

        # out of range page
        response = self.client.open(
            '/api/v1/c?page=0',
            method='GET'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # non int page
        response = self.client.open(
            '/api/v1/c?page=not_int',
            method='GET'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
