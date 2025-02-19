# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

from tol.api_base.auth import (
    AuthError,
    AuthManager,
    StateNotFoundError
)


class TestAuthBlueprint:
    """
    `auth_blueprint` calls the correct methods on
    `AuthManager`.
    """

    def test_login(
        self,
        client: FlaskClient,
        auth_manager: AuthManager
    ) -> None:
        """
        Http-GET to `/auth/login` calls
        `AuthManager().login()` without arguments.
        """

        json = {
            'loginUrl': 'http://test.lan/?hype=train'
        }

        auth_manager.login.return_value = json
        auth_manager.login.assert_not_called()

        res = client.get('/auth/login')

        auth_manager.login.assert_called_once_with()
        assert res.status_code == 200
        assert res.json == json

    def test_get_token_from_callback(
        self,
        client: FlaskClient,
        auth_manager: AuthManager
    ) -> None:
        """
        Http-POST to `/auth/token` calls
        `AuthManager().get_token_from_callback()`
        with the parsed request body.
        """

        json = {
            'test': True,
            'meaningless': 'yes'
        }

        auth_manager.get_token_from_callback.return_value = json
        auth_manager.get_token_from_callback.assert_not_called()

        res = client.post(
            '/auth/token',
            json={
                'state': 'hype-train',
                'code': 'fun'
            }
        )

        auth_manager.get_token_from_callback.assert_called_once_with(
            'hype-train',
            'fun'
        )
        assert res.status_code == 200
        assert res.json == json

    def test_create_user_profile(
        self,
        client: FlaskClient,
        auth_manager: AuthManager
    ) -> None:
        """
        Http-POST to `/auth/profile` calls
        `AuthManager().create_user_profile()`
        with the parsed request body.
        """

        json = {
            'test': True,
            'meaningless': 'yes'
        }

        auth_manager.create_user_profile.return_value = json
        auth_manager.create_user_profile.assert_not_called()

        res = client.post(
            '/auth/profile',
            json={
                'token': 'hype-train'
            }
        )

        auth_manager.create_user_profile.assert_called_once_with(
            'hype-train'
        )
        assert res.status_code == 200
        assert res.json == json


class TestAuthError:
    """
    All children of `AuthError` are handled correctly.
    """

    def test_state_not_found(
        self,
        client: FlaskClient,
        auth_manager: AuthManager
    ) -> None:
        """Raise `StateNotFoundError` -> 400"""

        auth_manager.get_token_from_callback.side_effect = (
            StateNotFoundError()
        )

        res = client.post(
            '/auth/token',
            json={
                'state': 'this will fail!!!',
                'code': 'fun'
            }
        )

        assert res.status_code == 400

    def test_custom(
        self,
        client: FlaskClient,
        auth_manager: AuthManager
    ) -> None:
        """
        A custom error with pinned error messages is rendered
        predictably.
        """

        class CustomError(AuthError):
            def __init__(self) -> None:
                super().__init__(
                    451,
                    'Fahrenheit',
                    'A book is a loaded gun'
                )

        auth_manager.login.side_effect = CustomError()

        res = client.get('/auth/login')

        assert res.status_code == 451
        assert res.json == {
            'errors': [
                {
                    'title': 'Fahrenheit',
                    'detail': 'A book is a loaded gun'
                }
            ]
        }
