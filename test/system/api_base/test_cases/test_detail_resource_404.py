# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestDetailResource404(BaseTestCase):
    def test_get_b_404(self):
        response = self.client.open(
            '/api/v1/b/9999',
            method='GET',
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_get_c_404(self):
        response = self.client.open(
            '/api/v1/b/9999',
            method='GET',
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_get_d_404(self):
        response = self.client.open(
            '/api/v1/b/9999',
            method='GET',
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_delete_b_404(self):
        response = self.client.open(
            '/api/v1/b/9999',
            method='DELETE',
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_delete_c_404(self):
        response = self.client.open(
            '/api/v1/c/9999',
            method='DELETE',
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_delete_d_404(self):
        response = self.client.open(
            '/api/v1/d/9999',
            method='DELETE',
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_patch_b_404(self):
        response = self.client.open(
            '/api/v1/b/9999',
            method='PATCH',
            json={
                'data': {
                    'attributes': {
                        'a_id': 0
                    },
                    'type': 'b'
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_patch_c_404(self):
        response = self.client.open(
            '/api/v1/c/9999',
            method='PATCH',
            json={
                'data': {
                    'type': 'c',
                    'attributes': {
                        'nullable_column': 'test_string'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_patch_d_404(self):
        response = self.client.open(
            '/api/v1/d/9999',
            method='PATCH',
            json={
                'data': {
                    'type': 'd',
                    'attributes': {
                        'non_nullable_column': 'ANOTHER TEST STRING'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
