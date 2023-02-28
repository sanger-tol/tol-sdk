# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestEnumMethodsByName(BaseTestCase):
    def test_i_get_by_name_200(self):
        self.add_i(id=348598, name='testing')
        # get by name
        response = self.client.open(
            '/api/v1/enum/i/testing',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that the response is correct
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'i',
                    'id': '348598',
                    'attributes': {
                        'name': 'testing',
                        'description': None
                    },
                    'relationships': {
                        'j': {
                            'links': {
                                'related': '/enum/i/testing/j'
                            }
                        }
                    }
                }
            }
        )

    def test_i_get_by_bad_name_404(self):
        # add an irrelevant I
        self.add_i(id=348523, name='nice')
        # get a non-existent name
        response = self.client.open(
            '/api/v1/enum/i/not_nice',
            method='GET'
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_no_override_id_by_name_patch_400(self):
        # add an I
        self.add_i(id=4989, name='happy')
        # attempt to patch to a new id
        response = self.client.open(
            '/api/v1/enum/i/happy',
            method='PATCH',
            json={
                'data': {
                    'type': 'i',
                    'id': '1337',
                    'attributes': {
                        'name': 'dinosaur',
                        'description': 'This is a hacker.'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check it failed for the right reason
        self.assertEqual(
            response.json,
            {
                'errors': [{
                    'detail': 'Unknown field.',
                    'source': {
                        'pointer': '/data/id'
                    }
                }]
            }
        )
        # confirm that no state change occured
        response = self.client.open(
            '/api/v1/enum/i/happy',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'data': {
                    'id': '4989',
                    'type': 'i',
                    'attributes': {
                        'name': 'happy',
                        'description': None
                    },
                    'relationships': {
                        'j': {
                            'links': {
                                'related': '/enum/i/happy/j'
                            }
                        }
                    }
                }
            }
        )
        # assert that no new entry has been created
        response = self.client.open(
            '/api/v1/enum/i/dinosaur',
            method='GET'
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_override_name_by_name_patch_200(self):
        # add an I
        self.add_i(id=1480, name='nicely')
        # attempt to patch to a new id
        response = self.client.open(
            '/api/v1/enum/i/nicely',
            method='PATCH',
            json={
                'data': {
                    'type': 'i',
                    'attributes': {
                        'name': 'new'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that the name is overriden
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'i',
                    'id': '1480',
                    'attributes': {
                        'name': 'new',
                        'description': None
                    },
                    'relationships': {
                        'j': {
                            'links': {
                                'related': '/enum/i/new/j'
                            }
                        }
                    }
                }
            }
        )

    def test_delete_by_name_i(self):
        self.add_i(id=34989, name='day', description='quaint')

        # delete the instance by name
        response = self.client.open(
            '/api/v1/enum/i/day',
            method='DELETE',
            headers=self._get_auth_user_1_headers()
        )
        self.assert_status(response, 204)

        # confirm that it is no longer in the db
        response = self.client.open(
            '/api/v1/enum/i/day',
            method='GET'
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_equivalent_methods_list_get_i_and_j(self):
        # add the data
        self.add_i(id=878, name='excellent')
        self.add_j(id=909090, i='excellent')
        self.add_j(id=8374483, i='excellent')
        self.add_j(id=987, i='excellent')

        # the expected data (should be identical for both)
        expected_data = {
            'meta': {
                'page': 1,
                'page_size': 20,
                'offset': 0,
                'limit': 20,
                'total': 3
            },
            'data': [
                {
                    'type': 'j',
                    'id': '987',
                    'attributes': {
                        'i': 'excellent'
                    }
                },
                {
                    'type': 'j',
                    'id': '909090',
                    'attributes': {
                        'i': 'excellent'
                    }
                },
                {
                    'type': 'j',
                    'id': '8374483',
                    'attributes': {
                        'i': 'excellent'
                    }
                },
            ]
        }

        # J-relation list get on I
        first_response = self.client.open(
            '/api/v1/enum/i/excellent/j',
            method='GET'
        )
        self.assert200(
            first_response,
            f'Response body is : {first_response.data.decode("utf-8")}'
        )
        # assert that the data is correct
        self.assertEqual(first_response.json, expected_data)

        # list-get on J, filter by I=excellent
        second_response = self.client.open(
            '/api/v1/j?filter={"exact":{"i":"excellent"}}',
            method='GET'
        )
        self.assert200(
            second_response,
            f'Response body is : {second_response.data.decode("utf-8")}'
        )
        # assert that the data is correct
        self.assertEqual(second_response.json, expected_data)
