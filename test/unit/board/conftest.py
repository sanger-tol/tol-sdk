# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base2.misc import AuthContext
from tol.api_client2.view import View
from tol.board import dashboard_blueprint
from tol.core import (
    DataSource,
    OperableDataSource
)
from tol.core.operator import (
    DetailGetter,
    PageGetter,
    Relational
)


@pytest.fixture
def ds() -> OperableDataSource:
    ds_class = type(
        '',
        (
            DataSource,
            DetailGetter,
            PageGetter,
            Relational,
        ),
        {}
    )

    mock_ds: OperableDataSource = create_autospec(
        ds_class,
        spec_set=True
    )

    mock_ds.supported_types = [
        'component',
        'component_zone',
        'zone',
        'zone_view',
        'view',
        'view_board',
        'board',
        'user'
    ]

    return mock_ds


@pytest.fixture
def ctx() -> AuthContext:
    return create_autospec(
        AuthContext,
        spec_set=True
    )


@pytest.fixture
def view() -> View:
    return create_autospec(
        View,
        spec_set=True
    )


@pytest.fixture
def admin_role() -> str:
    return 'adminzzzz'


@pytest.fixture
def app(
    ds: OperableDataSource,
    ctx: AuthContext,
    view: View,
    admin_role: str,
) -> Flask:

    app = Flask(__name__)
    app.testing = True

    bp = dashboard_blueprint(
        ds,
        admin_role=admin_role,
        ctx_getter=lambda: ctx,
        view_factory=lambda: view
    )
    app.register_blueprint(bp)

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
