# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Blueprint, Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.board import board_blueprint
from tol.sql import SqlDataSource


@pytest.fixture(scope='package')
def type_hierarchy() -> list[str]:
    """
    Imitates the (descending-order) type
    hierarchy (at time of writing):

    - board
    - view
    - zone
    - component
    """

    return ['L', 'M', 'S']


@pytest.fixture
def board_ds(
    type_hierarchy: list[str]
) -> SqlDataSource:

    mock_ds: SqlDataSource = create_autospec(
        SqlDataSource,
        spec_set=True
    )

    mock_ds.supported_types = type_hierarchy
    mock_ds.attribute_types = {
        t: {} for t in type_hierarchy
    }

    return mock_ds


@pytest.fixture
def board_auth_ctx() -> AuthContext:
    return AuthContext()


@pytest.fixture
def board_bp(
    board_ds: SqlDataSource,
    board_auth_ctx: AuthContext,
    type_hierarchy: list[str]
) -> Blueprint:

    return board_blueprint(
        board_ds,
        type_hierarchy=type_hierarchy,
        ctx_getter=lambda: board_auth_ctx
    )


@pytest.fixture
def board_app(board_bp: Blueprint) -> Flask:
    app = Flask(__name__)
    app.testing = True
    app.register_blueprint(board_bp)

    return app


@pytest.fixture
def board_client(board_app: Flask) -> FlaskClient:
    return board_app.test_client()
