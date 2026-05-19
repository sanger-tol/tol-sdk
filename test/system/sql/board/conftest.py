# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Blueprint, Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.board import board_blueprint
from tol.board.constants import TYPE_HIERARCHY
from tol.core import core_data_object
from tol.sql import (
    Model,
    SqlDataSource,
    create_sql_datasource
)


@pytest.fixture
def board_auth_ctx() -> AuthContext:
    return AuthContext()


@pytest.fixture(scope='package')
def type_hierarchy() -> list[str]:
    return TYPE_HIERARCHY


@pytest.fixture
def board_ds(
    db_uri: str,
    models_list: list[Model]
) -> SqlDataSource:

    sql_ds = create_sql_datasource(
        models_list,
        db_uri
    )
    core_data_object(sql_ds)

    return sql_ds


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
