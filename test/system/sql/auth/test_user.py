# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

import responses

from tol.api_base.auth import OidcConfig
from tol.sql.auth.models import AuthUser


@pytest.fixture(scope='module')
def user_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'user'
    ]
    return matches[0]


class TestUser:

    @responses.activate
    def test_userinfo__extra_oidc_fields(
        self,
        session_factory,
        user_model: AuthUser,
        oidc_config: OidcConfig,
        client: FlaskClient
    ):
        """
        extra fields on OIDC userinfo endpoint
        return -> they are stored using
        the mapping.
        """

        user_info = {
            'email': 'test@test.lol',
            'do_not_forget_me': "I won't!",
            'me_neither': 202
        }

        responses.get(
            oidc_config.user_info_url,
            json=user_info
        )

        r = client.post(
            '/auth/profile',
            json={
                'token': 'does not matter at all'
            }
        )
        assert r.status_code == 200, r.text

        # check the user has the correct
        # extra fields
        with session_factory() as sess:
            user = sess.query(
                user_model
            ).filter_by(
                changed_lol='test@test.lol'
            ).first()

            assert (
                user.extra_oidc_field == "I won't!"
            )
            assert (
                user.extra_oidc_int == 202
            )
