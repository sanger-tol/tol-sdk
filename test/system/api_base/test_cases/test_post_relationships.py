# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestPostRelationships(BaseTestCase):
    def test_post_b_good_relationship_201(self):
        self.add_a(id=300)

        response = self.client.open(
            '/api/v1/B',
            method='POST',
            json={
                'data': {
                    'type': 'B',
                    'attributes': {},
                    'relationships': {
                        'A': {
                            'data': {
                                'type': 'A',
                                'id': '300'
                            }
                        }
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert201(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        id_ = response.json['data']['id']
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'B',
                    'id': id_,
                    'relationships': {
                        'A': {
                            'links': {
                                'related': '/A/300'
                            },
                            'data': {
                                'type': 'A',
                                'id': '300'
                            }
                        },
                        'E': {
                            'links': {
                                'related': f'/B/{id_}/E'
                            }
                        }
                    }
                }
            }
        )

    def test_post_b_bad_relationship_400(self):
        self.add_a(id=300)

        response = self.client.open(
            '/api/v1/B',
            method='POST',
            json={
                'data': {
                    'type': 'B',
                    'attributes': {},
                    'relationships': {
                        'A': {
                            'data': {
                                'type': 'A',
                                'id': '57900'
                            }
                        }
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
