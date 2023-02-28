# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestColumnNullabilityPost(BaseTestCase):
    def test_collumn_nullabillity_post_c_no_error(self):
        response = self.client.open(
            '/api/v1/c',
            method='POST',
            json={
                'data': {
                    'type': 'c',
                    'attributes': {
                        'other_column': 'no matter'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert201(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'c',
                    'attributes': {
                        'other_column': 'no matter',
                        'nullable_column': None
                    },
                    'id': response.json['data']['id']
                },
            }
        )

    def test_non_nullable_column_omitted_post_d_error(self):
        response = self.client.open(
            '/api/v1/d',
            method='POST',
            json={
                'data': {
                    'type': 'd',
                    'attributes': {
                        'other_column': 'no matter'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
