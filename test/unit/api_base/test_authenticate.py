# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import MagicMock, Mock, PropertyMock

from flask import Flask, request

from flask_testing import TestCase

import pytest

from tol.api_base.blueprint import _core_blueprint
from tol.api_base.misc import AuthContext, quick_and_dirty_auth
from tol.api_base.misc.auth_context import default_ctx_getter
from tol.api_client.exception import UnauthenticatedError
from tol.core import DataSource
from tol.core.operator import Deleter, DetailGetter


class _MockDataSource(DataSource, DetailGetter, Deleter):

    def __init__(self, config: dict[str, Any], ctx_getter=None):
        self.__ctx_getter = ctx_getter
        super().__init__(config, [])

    def get_by_id(self, object_type: str, object_ids, **kwargs):
        assert len(object_ids) == 1

        # get the global user ID
        user_id = self.__ctx_getter().user_id

        mock_object = MagicMock()
        type(mock_object).type = PropertyMock(
            return_value=object_type
        )
        type(mock_object).id = PropertyMock(
            return_value=object_ids[0]
        )
        type(mock_object).attributes = PropertyMock(
            return_value={'user_id': user_id}
        )

        return [
            mock_object
        ]

    def delete(self, object_type: str, object_ids: Iterable[str]) -> None:
        pass

    @property
    def attribute_types(self) -> dict:
        return {}

    @property
    def supported_types(self) -> list[str]:
        return ['lol']


class TestAuthenticator(TestCase):
    def mock_authenticate(self, __ctx: AuthContext) -> None:
        token = request.headers.get('token')
        if token != 'hello_world':
            raise UnauthenticatedError('say hi first!')

    def mock_ctx_get(self):
        ctx = Mock()
        self.__user_id_prop = PropertyMock(return_value='hi')
        type(ctx).user_id = self.__user_id_prop
        return ctx

    def create_app(self):
        app = Flask(__name__)
        app.testing = True

        blueprint = _core_blueprint(
            {'lol': _MockDataSource({}, ctx_getter=self.mock_ctx_get)},
            '/data'
        )
        app.register_blueprint(blueprint)

        @app.before_request
        def authenticate() -> None:
            auth_context = self.mock_ctx_get()
            self.mock_authenticate(auth_context)
        return app

    def test_no_token(self):
        """no token -> 401"""
        response = self.client.open('/data/lol/32')
        self.assert401(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_invalid_token(self):
        """token does not match a user -> 401"""

        response = self.client.open(
            '/data/lol/32',
            headers={
                'token': "lol won't work"
            }
        )
        self.assert401(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_valid_token(self):
        """
        token does match a user:

        - user_id is set
        - return 200
        """

        response = self.client.open(
            '/data/lol/32',
            headers={
                'token': 'hello_world'
            }
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        expected = {
            'data': {
                'type': 'lol',
                'id': '32',
                'attributes': {
                    'user_id': 'hi'  # the set user id is returned
                }
            }
        }
        assert response.json == expected


class TestQuickAndDirtyAuth:
    """Test outside of a flask app"""

    def test_no_token(self):
        """provide no token -> 401"""

        auth = quick_and_dirty_auth(
            'all-powerful',
            token_getter=lambda _: None,
            method_getter=lambda: 'POST'
        )
        with pytest.raises(UnauthenticatedError):
            auth(MagicMock())

    def test_bad_token(self):
        """provide invalid token -> 401"""

        auth = quick_and_dirty_auth(
            'all-powerful',
            token_getter=lambda _: 'bad-token',
            method_getter=lambda: 'POST'
        )
        with pytest.raises(UnauthenticatedError):
            auth(MagicMock())

    def test_good_token(self):
        """provide good token -> no error"""

        auth = quick_and_dirty_auth(
            'all-powerful',
            token_getter=lambda _: 'all-powerful',
            method_getter=lambda: 'POST'
        )
        auth(MagicMock())


class TestQuickAndDirtyAuthFlask(TestCase):
    """Test `quick_and_dirty_auth` in app"""

    def create_app(self):
        app = Flask(__name__)
        app.testing = True

        blueprint = _core_blueprint(
            {'lol': _MockDataSource({}, ctx_getter=default_ctx_getter)},
            '/data'
        )
        app.register_blueprint(blueprint)

        authenticator = quick_and_dirty_auth(
            'test-token',
            excluded_methods=['DELETE']
        )

        @app.before_request
        def authenticate() -> None:
            auth_context = default_ctx_getter()
            authenticator(auth_context)

        return app

    def test_no_token(self):
        """no token -> 401"""

        response = self.client.open(
            '/data/lol/32'
        )
        self.assert401(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_bad_token(self):
        """invalid token -> 401"""

        response = self.client.open(
            '/data/lol',
            headers={'token': 'asdklsad8'}
        )
        self.assert401(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_excluded_method(self):
        """method is excluded -> 200 regardless of (no) token"""

        # no token at all
        response = self.client.open(
            '/data/lol/32',
            method='DELETE'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # invalid token
        response = self.client.open(
            '/data/lol/32',
            method='DELETE',
            headers={'token': 'BAAAADDD'}
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_good_token(self):
        """good token -> 200"""

        response = self.client.open(
            '/data/lol/32',
            headers={'token': 'test-token'}
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
