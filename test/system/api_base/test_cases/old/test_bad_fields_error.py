# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from ...test_case import BaseTestCase


class TestBadFieldsError(BaseTestCase):
    def test_b_id_in_request_body_post_400(self):
        self.add_a(id=9090)
        response = self.client.open(
            '/api/v1/b',
            method='POST',
            json={
                'data': {
                    'id': 9999,
                    'type': 'b',
                    'relationships': {
                        'a': {
                            'data': {
                                'type': 'a',
                                'id': 9090
                            }
                        }
                    }
                },
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
