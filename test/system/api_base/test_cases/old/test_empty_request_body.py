# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestEmptyRequestBody(BaseTestCase):
    def test_post_d_with_empty_request_body_400(self):
        response = self.client.open(
            '/api/v1/d',
            method='POST',
            json={},
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_post_d_with_no_data_400(self):
        response = self.client.open(
            '/api/v1/d',
            method='POST',
            json={
                'data': {
                    'type': 'D',
                    'attributes': {}
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_patch_c_with_empty_request_body_400(self):
        self.add_c(id=9099)
        response = self.client.open(
            '/api/v1/c/9099',
            method='PATCH',
            json={},
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_patch_c_with_no_attributes_200(self):
        self.add_c(id=9099)
        response = self.client.open(
            '/api/v1/c/9099',
            method='PATCH',
            json={
                'data': {
                    'type': 'c',
                    'attributes': {}
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
