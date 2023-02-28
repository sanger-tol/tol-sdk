# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestDeleteWithDependant400(BaseTestCase):
    def test_delete_b_with_dependant_e_400(self):
        self.add_a(id=20)
        self.add_b(id=30, a_id=20)
        self.add_e(id=40, b_id=30)

        response = self.client.open(
            '/api/v1/b/30',
            method='DELETE',
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
