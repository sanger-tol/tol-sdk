# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base import pipeline_steps_blueprint
from tol.api_base.misc import AuthContext
from tol.prefect import PrefectDataSource
from tol.sql import SqlDataSource


@pytest.fixture(scope='package')
def role() -> str:
    return 'ambiguous_role'


@pytest.fixture
def ctx() -> AuthContext:
    return AuthContext()


@pytest.fixture
def sql_ds() -> SqlDataSource:
    __ds: SqlDataSource = create_autospec(
        SqlDataSource,
        spec_set=True
    )

    __ds.supported_types = [
        'pipeline',
        'pipeline_step',
        'upload'
    ]

    __ds.attribute_types = {
        k: {}
        for k in __ds.supported_types
    }

    return __ds


@pytest.fixture
def prefect_ds() -> PrefectDataSource:
    __ds: PrefectDataSource = create_autospec(
        PrefectDataSource,
        spec_set=True
    )

    __ds.supported_types = ['flow_run']

    __ds.attribute_types = {
        'flow_run': {}
    }

    return __ds


@pytest.fixture
def app(
    role: str,
    ctx: AuthContext,
    sql_ds: SqlDataSource,
    prefect_ds: PrefectDataSource
) -> Flask:

    __app = Flask(__name__)
    __app.testing = True

    bp = pipeline_steps_blueprint(
        sql_ds,
        prefect_ds,
        role=role,
        ctx_getter=lambda: ctx
    )

    __app.register_blueprint(bp)

    return __app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
