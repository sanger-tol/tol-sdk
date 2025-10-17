# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from inspect import BoundArguments
from typing import Optional
from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base import data_blueprint
from tol.api_base.auth import (
    AuthError,
    AuthInspector,
    basic_auth_inspector,
    require_auth
)
from tol.api_base.auth.error import ForbiddenError
from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSource, OperableDataSource, ReqFieldsTree
from tol.core.datasource_filter import AndFilter, DataSourceFilter
from tol.core.operator import (
    Deleter,
    DetailGetter,
    OperatorMethod,
    PageGetter
)


class TestRequireAuth:
    """
    `require_auth` raises the correct exceptions when needed,
    and doesn't obstruct when not.
    """

    def test_no_role_specified(self):
        """no `role` kwarg is given to `require_auth`"""

        mock_ctx = create_autospec(AuthContext, spec_set=True)
        mock_ctx.roles = []

        @require_auth(ctx_getter=lambda: mock_ctx)
        def _mock():
            pass

        _mock()

    def test_no_roles(self):
        """`roles` is an empty list"""

        mock_ctx = create_autospec(AuthContext, spec_set=True)
        mock_ctx.roles = []

        @require_auth(
            role='admin',
            ctx_getter=lambda: mock_ctx
        )
        def _mock():
            pass

        with pytest.raises(AuthError) as e:
            _mock()

        assert e.value.status_code == 403

    def test_irrelevant_roles(self):
        """`roles` is populated, but with the wrong ones"""

        mock_ctx = create_autospec(AuthContext, spec_set=True)
        mock_ctx.roles = ['hype', 'train']

        @require_auth(
            role='admin',
            ctx_getter=lambda: mock_ctx
        )
        def _mock():
            pass

        with pytest.raises(AuthError) as e:
            _mock()

        assert e.value.status_code == 403

    def test_good(self):
        """
        a `role` kwarg is given, and is in the context's `roles` - no
        obstruction
        """

        mock_ctx = create_autospec(AuthContext, spec_set=True)
        mock_ctx.roles = ['admin', 'another']

        @require_auth(
            role='admin',
            ctx_getter=lambda: mock_ctx
        )
        def _mock():
            pass

        _mock()


@pytest.fixture
def inspector() -> AuthInspector:

    def __inspect(
        object_type: str,
        operation: str,
        bound_args: BoundArguments
    ) -> Optional[AndFilter]:

        if object_type == 'a' and operation != OperatorMethod.DETAIL:
            raise ForbiddenError()

        if object_type == 'b' and operation == OperatorMethod.PAGE:
            return {
                'user.id': {
                    'eq': {
                        'value': 'random_ID'
                    }
                }
            }

    return __inspect


@pytest.fixture
def mock_obj() -> DataObject:
    mock_obj = create_autospec(DataObject, spec_set=True)
    mock_obj.attributes = {}
    mock_obj.type = 'a'
    mock_obj.id = '999999'

    return mock_obj


@pytest.fixture
def mock_ds(mock_obj: DataObject) -> DataSource:

    class _MockDs(
        DataSource,
        DetailGetter,
        Deleter,
        PageGetter
    ):
        pass

    _mock = create_autospec(_MockDs, spec_set=True)
    _mock.supported_types = ['a', 'b', 'c']
    _mock.get_attribute_types.return_value = {}

    _mock.get_by_id.return_value = [mock_obj]
    _mock.get_page_size.return_value = 10
    _mock.get_list_page.return_value = ([], 0)

    return _mock


@pytest.fixture
def app(
    mock_ds: DataSource,
    inspector: AuthInspector
) -> Flask:

    app_fixture = Flask(__name__)
    app_fixture.testing = True

    data_bp = data_blueprint(
        mock_ds,
        auth_inspector=inspector
    )
    app_fixture.register_blueprint(data_bp)

    return app_fixture


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


class TestAuthInspector:
    """
    The given `AuthInspector` function raises a 403 error on insufficient
    permissions, and does not obstruct otherwise.
    """

    def test_bad(self, client: FlaskClient):
        """A forbidden scenario (DELETE on 'a') raises 403"""

        res = client.delete('/data/a/999999')
        assert res.status_code == 403

    def test_good(self, client: FlaskClient):
        """No problems -> no obstruction"""

        res = client.get('/data/a/999999')
        assert res.status_code == 200


@pytest.fixture
def basic_role() -> str:
    return 'fun-times'


@pytest.fixture(scope='function')
def auth_ctx() -> AuthContext:
    ctx: AuthContext = create_autospec(AuthContext, spec_set=True)
    ctx.user_id = 101

    return ctx


@pytest.fixture(scope='function')
def basic_inspector(
    basic_role: str,
    auth_ctx: AuthContext
) -> AuthInspector:

    return basic_auth_inspector(
        basic_role,
        ctx_getter=lambda: auth_ctx,
    )


class TestBasicAuthInspector:
    """
    `basic_auth_inspector` always permits read-only access, and raises a
    `ForbiddenError` if not authenticated with the `basic_role` otherwise.
    """

    def test_readonly(
        self,
        basic_inspector: AuthInspector,
        auth_ctx: AuthContext
    ):
        """
        all readonly methods don't raise `ForbiddenError`, even without
        any roles.
        """

        auth_ctx.roles = []

        basic_inspector(
            'does-not-matter',
            OperatorMethod.COUNT,
            bound_args=None,
        )

    def test_readonly_with_good_role(
        self,
        basic_role: str,
        basic_inspector: AuthInspector,
        auth_ctx: AuthContext
    ):
        """
        all readonly methods don't raise `ForbiddenError`, even when
        a good role is specified.
        """

        auth_ctx.roles = [basic_role]

        basic_inspector(
            'does-not-matter',
            OperatorMethod.AGGREGATE,
            bound_args=None,
        )

    def test_write_bad_roles(
        self,
        basic_inspector: AuthInspector,
        auth_ctx: AuthContext
    ):
        """
        a protected write method, with irrelevant roles that aren't the basic one,
        raises a `ForbiddenError`.
        """

        auth_ctx.roles = ['hype', 'train']

        with pytest.raises(ForbiddenError):
            basic_inspector(
                'no-delete----only-read',
                OperatorMethod.DELETE,
                bound_args=None,
            )

    def test_write_good_role(
        self,
        basic_role: str,
        basic_inspector: AuthInspector,
        auth_ctx: AuthContext
    ):
        """
        a protected write method, with the correct `basic_role`, is permitted.
        """

        auth_ctx.roles = [basic_role]

        basic_inspector(
            'does-not-matter',
            OperatorMethod.UPSERT,
            bound_args=None,
        )


class TestFilter:
    """
    an `AuthInspector`, if provided, will update filters.
    """

    def test_adds_and_filter(
        self,
        client: FlaskClient,
        mock_ds: OperableDataSource
    ):
        """Returning `AndFilter` -> update"""

        # no filter specified
        client.get('/data/b')
        mock_ds.get_list_page.assert_called_once_with(
            'b',
            1,
            page_size=None,
            object_filters=DataSourceFilter(
                and_={
                    'user.id': {
                        'eq': {
                            'value': 'random_ID'
                        }
                    }
                }
            ),
            sort_by=None,
            requested_tree=ReqFieldsTree('b', mock_ds),
        )

        mock_ds.reset_mock()

        # and_ filter specified
        client.get(
            '/data/b',
            query_string={
                'filter': json.dumps(
                    {
                        'and_': {
                            'lol': {
                                'eq': {
                                    'value': 'hiiii',
                                    'negate': True
                                }
                            }
                        }
                    }
                )
            }
        )
        mock_ds.get_list_page.assert_called_once_with(
            'b',
            1,
            page_size=None,
            object_filters=DataSourceFilter(
                and_={
                    'user.id': {
                        'eq': {
                            'value': 'random_ID'
                        }
                    },
                    'lol': {
                        'eq': {
                            'value': 'hiiii',
                            'negate': True
                        }
                    }
                }
            ),
            sort_by=None,
            requested_tree=ReqFieldsTree('b', mock_ds),
        )

    def test_none(
        self,
        client: FlaskClient,
        mock_ds: DataSource
    ):
        """Returning `None` -> no update"""

        # no filter specified
        client.get('/data/c')
        mock_ds.get_list_page.assert_called_once_with(
            'c',
            1,
            page_size=None,
            object_filters=None,
            sort_by=None,
            requested_tree=ReqFieldsTree('c', mock_ds),
        )

        mock_ds.reset_mock()

        # and_ filter specified
        client.get(
            '/data/c',
            query_string={
                'filter': json.dumps(
                    {
                        'and_': {
                            'lol': {
                                'eq': {
                                    'value': 'hiiii',
                                    'negate': True
                                }
                            }
                        }
                    }
                )
            }
        )
        mock_ds.get_list_page.assert_called_once_with(
            'c',
            1,
            page_size=None,
            object_filters=DataSourceFilter(
                and_={
                    'lol': {
                        'eq': {
                            'value': 'hiiii',
                            'negate': True
                        }
                    }
                }
            ),
            sort_by=None,
            requested_tree=ReqFieldsTree('c', mock_ds),
        )
