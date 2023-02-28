# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestEnumRelationListGet(BaseTestCase):
    def test_i_relation_on_j_list_get_200(self):
        # add two I's
        self.add_i(id=34091, name='thing1')
        self.add_i(id=981234, name='thing3')
        # add some J's
        self.add_j(id=878934, i='thing3')
        self.add_j(id=98823, i='thing1')
        self.add_j(id=3453290, i='thing1')

        # get thing3's J's
        response = self.client.open(
            '/api/v1/enum/i/thing3/j',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that the correct one is returned
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 1
                },
                'data': [{
                    'type': 'j',
                    'id': '878934',
                    'attributes': {
                        'i': 'thing3'
                    }
                }]
            }
        )

        # get thing1's J's, in descending order of id
        response = self.client.open(
            '/api/v1/enum/i/thing1/j?sort_by=-id',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that the correct one is returned
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
                        'type': 'j',
                        'id': '3453290',
                        'attributes': {
                            'i': 'thing1'
                        }
                    },
                    {
                        'type': 'j',
                        'id': '98823',
                        'attributes': {
                            'i': 'thing1'
                        }
                    }
                ]
            }
        )

    def test_i_bad_name_relation_on_j_list_get_404(self):
        # add an I
        self.add_i(id=98902, name='thing2')
        # try to get the J's of a non-existent I
        response = self.client.open(
            '/api/v1/enum/i/nothing/j',
            method='GET'
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that it failed for the right reason
        self.assertEqual(
            response.json,
            {
                'errors': [{
                    'title': 'Not Found',
                    'detail': "No name 'nothing' exists on enum i."
                }]
            }
        )
