# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from base64 import b64encode
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from flask.testing import FlaskClient

import pytest

import responses
from responses.matchers import (
    header_matcher,
    urlencoded_params_matcher
)

from sqlalchemy import select

from tol.api_base2.auth import OidcConfig


@pytest.fixture(scope='module')
def state_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'oidc_state'
    ]
    return matches[0]


class TestState:
    """Tests OIDC auth state"""

    def test_login__old_state_deleted(
        self,
        state_model,
        session_factory,
        client: FlaskClient
    ):
        """
        States older than 1 hour are deleted on `/login`.
        """

        self.__add_states(state_model, session_factory)

        client.get('/auth/login')

        self.__assert_only_recent(state_model, session_factory)

    def test_login__state_added(
        self,
        state_model,
        session_factory,
        client: FlaskClient,
        oidc_config: OidcConfig
    ):
        """
        Calling `/login` endpoint (succesfully) creates 1 `State`
        in an empty DB, with the correct uuid.
        """

        res = client.get('/auth/login')
        login_url = res.json['loginUrl']

        self.__assert_login_url_correct(login_url, oidc_config)
        self.__assert_only_one_state(login_url, state_model, session_factory)

    @responses.activate
    def test_token__invalid_state(
        self,
        state_model,
        session_factory,
        client: FlaskClient
    ):
        """
        Calling `/token` endpoint with invalid state produces an error,
        and no states are deleted.
        """

        self.__add_states(state_model, session_factory)

        res = client.post(
            '/auth/token',
            json={
                'state': 'totally invalid - baseless even',
                'code': 'idk - lol!'
            }
        )

        assert res.status_code not in [200, 500]

        state_uuids = self.__get_state_uuids_in_db(
            state_model,
            session_factory
        )
        assert sorted(state_uuids) == [
            'old',
            'really old',
            'recent'
        ]

    @responses.activate
    def test_token__valid_state(
        self,
        state_model,
        session_factory,
        oidc_config: OidcConfig,
        client: FlaskClient
    ):
        """
        Calling `/token` endpoint with a valid state progresses
        fine.
        """

        self.__add_states(state_model, session_factory)

        auth = self.__basic_auth(
            oidc_config.client_id,
            oidc_config.client_secret
        )

        expected = {
            'hype': 'train',
            'nothing': 'less'
        }

        responses.post(
            oidc_config.token_url,
            match=[
                header_matcher(
                    {
                        'Authorization': auth
                    }
                ),
                urlencoded_params_matcher(
                    {
                        'grant_type': 'authorization_code',
                        'code': 'idk - lol!',
                        'redirect_uri': oidc_config.redirect_uri
                    }
                )
            ],
            json=expected
        )

        res = client.post(
            '/auth/token',
            json={
                'state': 'recent',
                'code': 'idk - lol!'
            }
        )

        assert res.status_code == 200
        assert res.json == expected

    def __add_states(
        self,
        state_model,
        session_factory
    ):
        with session_factory() as sess:
            # slightly too old state
            sess.add(
                state_model(
                    id='old',
                    created_at=datetime.now() - timedelta(
                        hours=1,
                        seconds=10
                    )
                )
            )
            # really old state
            sess.add(
                state_model(
                    id='really old',
                    created_at=datetime.now() - timedelta(days=300)
                )
            )
            # recent state
            sess.add(
                state_model(
                    id='recent',
                    created_at=datetime.now()
                )
            )
            sess.commit()

    def __assert_only_recent(
        self,
        state_model,
        session_factory
    ):

        with session_factory() as sess:
            stmt = select(state_model)
            rows = list(
                sess.execute(stmt)
            )

            # there will be two states:
            #
            # - our remaining one
            # - one added by login
            assert len(rows) == 2

            # find the one we added
            for row in rows:
                (recent, ) = row
                if recent.id == 'recent':
                    return
                assert recent.id not in (
                    'old',
                    'really old'
                )

            assert False, 'our state was not found'

    def __get_params(self, login_url: str) -> dict[str, str]:
        parsed = urlparse(login_url)

        return parse_qs(parsed.query)

    def __get_state_uuid(self, login_url: str) -> str:
        params = self.__get_params(login_url)
        (state_uuid, ) = params['state']

        return state_uuid

    def __assert_login_url_correct(
        self,
        login_url: str,
        oidc_config: OidcConfig
    ) -> None:
        """
        Asserts that the `login_url` is formatted correctly
        """

        params = self.__get_params(login_url)

        assert params['client_id'] == [oidc_config.client_id]
        assert params['response_type'] == ['code']
        assert params['redirect_uri'] == [oidc_config.redirect_uri]
        assert params['scope'] == ['openid profile email']

    def __assert_only_one_state(
        self,
        login_url: str,
        state_model,
        session_factory,
    ):

        state_uuid = self.__get_state_uuid(login_url)

        with session_factory() as sess:
            stmt = select(state_model).where(
                state_model.id == state_uuid
            )
            rows = list(
                sess.execute(stmt)
            )

            assert len(rows) == 1

    def __get_state_uuids_in_db(
        self,
        state_model,
        session_factory
    ) -> list[str]:

        with session_factory() as sess:
            stmt = select(state_model)
            rows = list(
                sess.execute(stmt)
            )

            return [
                r.id for (r,) in rows
            ]

    def __basic_auth(
        self,
        username: str,
        password: str
    ) -> str:

        encoded = b64encode(
            f'{username}:{password}'.encode('ascii')
        ).decode('ascii')

        return f'Basic {encoded}'
