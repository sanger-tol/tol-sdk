# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestPostRelationships(BaseTestCase):
    def test_post_b_bad_relationship_400(self):
        self.add_a(id=300)

        response = self.client.open(
            '/api/v1/b',
            method='POST',
            json={
                'data': {
                    'type': 'b',
                    'attributes': {},
                    'relationships': {
                        'a': {
                            'data': {
                                'type': 'a',
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
