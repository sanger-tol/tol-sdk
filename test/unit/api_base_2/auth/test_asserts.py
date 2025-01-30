# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Optional
from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base2 import data_blueprint
from tol.api_base2.auth import (
    AuthError,
    AuthInspector,
    basic_auth_inspector,
    require_auth
)
from tol.api_base2.auth.error import ForbiddenError
from tol.api_base2.misc import AuthContext
from tol.core import DataObject, DataSource, OperableDataSource
from tol.core.datasource_filter import AndFilter, DataSourceFilter
from tol.core.operator import (
    Deleter,
    DetailGetter,
    OperatorMethod,
    PageGetter
)


@pytest.fixture
def inspector() -> AuthInspector:

    def __inspect(
        object_type: str,
        operation: str
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
        ctx_getter=lambda: auth_ctx
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
        )
