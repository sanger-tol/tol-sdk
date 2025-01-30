# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta

from flask import Flask
from flask.testing import FlaskClient

import pytest

import responses
from responses.matchers import header_matcher

from sqlalchemy import select

from tol.api_base2.auth import OidcConfig
from tol.api_base2.misc import default_ctx_getter


@pytest.fixture(scope='module')
def token_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'token'
    ]
    return matches[0]


@pytest.fixture(scope='module')
def user_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'user'
    ]
    return matches[0]


class TestToken:
    """Tests OIDC auth token."""

    def test_login__expired_tokens_deleted(
        self,
        token_model,
        user_model,
        session_factory,
        client: FlaskClient
    ):
        """
        Tokens older than 7 days are deleted on login.
        """

        self.__add_tokens(token_model, user_model, session_factory)

        client.get('/auth/login')

        self.__assert_no_expired(token_model, session_factory)

    @responses.activate
    def test_userinfo__existing_user(
        self,
        token_model,
        user_model,
        session_factory,
        oidc_config: OidcConfig,
        client: FlaskClient
    ):
        """
        `/userinfo` with existing user produces a new token
        """

        user_info = {
            'email': 'existing@hype.train'
        }

        self.__add_existing_user(
            user_model,
            token_model,
            session_factory
        )

        responses.get(
            oidc_config.user_info_url,
            match=[
                header_matcher(
                    {
                        'Authorization': 'Bearer token-mine12378'
                    }
                )
            ],
            json=user_info
        )

        res = client.post(
            '/auth/profile',
            json={
                'token': 'token-mine12378'
            }
        )

        assert res.status_code == 200
        assert res.json['oidc_id'] == 'existing@hype.train'
        self.__assert_token_on_user(
            token_model,
            'token-mine12378',
            session_factory
        )

    @responses.activate
    def test_userinfo__new_user(
        self,
        token_model,
        user_model,
        session_factory,
        oidc_config: OidcConfig,
        client: FlaskClient
    ):
        """
        `/userinfo` with a new user produces a new token
        """

        user_info = {
            'email': 'new@hype.train'
        }

        self.__add_existing_user(
            user_model,
            token_model,
            session_factory
        )

        responses.get(
            oidc_config.user_info_url,
            match=[
                header_matcher(
                    {
                        'Authorization': 'Bearer token-mine12378'
                    }
                )
            ],
            json=user_info
        )

        res = client.post(
            '/auth/profile',
            json={
                'token': 'token-mine12378'
            }
        )

        new_user_id = self.__get_new_user_id(
            user_model,
            session_factory,
            'new@hype.train'
        )

        assert res.status_code == 200
        assert res.json['oidc_id'] == 'new@hype.train'
        self.__assert_token_on_user(
            token_model,
            'token-mine12378',
            session_factory,
            user_id=new_user_id
        )

    def test_authenticate__bad_token(
        self,
        token_model,
        user_model,
        session_factory,
        auth_app: Flask,
        client: FlaskClient
    ):
        """
        Calling a write endpoint with an uncrecognised
        token - no `user_id` set on flask context
        """

        self.__add_existing_user(
            user_model,
            token_model,
            session_factory
        )

        with auth_app.app_context():
            client.get(
                '/data/test/404',
                headers={
                    'Dummy-Token': 'downright bone-chilling'
                }
            )
            ctx = default_ctx_getter()

            assert ctx.authenticated is False

    def test_authenticate__good_token(
        self,
        token_model,
        user_model,
        session_factory,
        client: FlaskClient,
        auth_app: Flask
    ):
        """
        Calling a write endpoint with a known
        token - `user_id` is set on flask context
        """

        self.__add_existing_user(
            user_model,
            token_model,
            session_factory
        )

        with auth_app.app_context():
            client.get(
                '/data/test/404',
                headers={
                    'Dummy-Token': 'valid token'
                }
            )
            ctx = default_ctx_getter()

            assert ctx.user_id == '789'

    def __add_existing_user(
        self,
        user_model,
        token_model,
        session_factory
    ):
        with session_factory() as sess:
            sess.add(
                user_model(
                    id=789,
                    changed_lol='existing@hype.train'
                )
            )
            sess.add(
                token_model(
                    token='valid token',
                    user_id=789
                )
            )

            sess.commit()

    def __get_new_user_id(
        self,
        user_model,
        session_factory,
        changed_lol: str
    ) -> int:
        with session_factory() as sess:
            stmt = select(user_model).where(
                user_model.changed_lol == changed_lol
            )
            rows = list(
                sess.execute(stmt)
            )

            assert len(rows) == 1

            (new_user, ) = rows[0]

            return new_user.id

    def __assert_token_on_user(
        self,
        token_class,
        token: str,
        session_factory,
        user_id: int = 789
    ):
        with session_factory() as sess:
            stmt = select(token_class).where(
                token_class.token == token
            ).where(
                token_class.user_id == user_id
            )
            rows = list(
                sess.execute(stmt)
            )

            assert len(rows) > 0

    def __add_tokens(
        self,
        token_model,
        user_model,
        session_factory
    ):
        with session_factory() as sess:
            # the user
            sess.add(
                user_model(
                    id=456,
                    changed_lol='test@hype.train'
                )
            )

            # slightly too old token
            sess.add(
                token_model(
                    id=1,
                    user_id=456,
                    token='tepid',
                    expires_at=datetime.now() - timedelta(seconds=10)
                )
            )
            # really old token
            sess.add(
                token_model(
                    id=2,
                    user_id=456,
                    token='ancient',
                    expires_at=datetime.now() - timedelta(days=3000)
                )
            )
            # recent, valid token
            sess.add(
                token_model(
                    id=3,
                    user_id=456,
                    token='just right',
                    expires_at=datetime.now() + timedelta(hours=1)
                )
            )
            sess.commit()

    def __assert_no_expired(
        self,
        token_model,
        session_factory
    ):

        with session_factory() as sess:
            stmt = select(token_model)
            rows = list(
                sess.execute(stmt)
            )

            assert len(rows) == 1

            (recent, ) = rows[0]
            assert recent.token == 'just right'
