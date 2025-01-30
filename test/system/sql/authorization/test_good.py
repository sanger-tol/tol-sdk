# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

from tol.core import OperableDataSource


class TestGood:
    """
        Golden path: User has Membership and Role required to
        access the resource
    """

    def test_delete(
        self,
        auth_mock_ds: OperableDataSource,
        client: FlaskClient
    ):

        r = client.delete(
            '/data_auth/sample/1',
            headers={
                'Dummy-Token': 'super_admin'
            }
        )
        assert r.status_code == 200

        auth_mock_ds.delete.assert_called_once_with(
            'sample',
            ['1']
        )
