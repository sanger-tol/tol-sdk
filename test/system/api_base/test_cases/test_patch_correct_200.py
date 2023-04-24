# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestUpdatedCorrectly200(BaseTestCase):
    def test_updated_correctly_b_200(self):
        a_id = 109
        new_a_id = 9090
        b_id = 218
        self.add_a(id=a_id)
        self.add_a(id=new_a_id)
        self.add_b(id_string=b_id, a_id=a_id)

        response = self.client.open(
            f'/api/v1/b/{b_id}',
            method='PATCH',
            json={
                'data': {
                    'type': 'b',
                    'relationships': {
                        'a': {
                            'data': {
                                'type': 'a',
                                'id': str(new_a_id)
                            }
                        }
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        self.assertEqual(
            response.json,
            {
                'data': {
                    'id': str(b_id),
                    'type': 'b',
                    'relationships': {
                        'a': {
                            'data': {
                                'id': str(new_a_id),
                                'type': 'a'
                            },
                            'links': {
                                'related': f'/a/{new_a_id}'
                            }
                        },
                        'e': {
                            'links': {
                                'related': f'/b/{b_id}/e'
                            }
                        }
                    }
                }
            }
        )
