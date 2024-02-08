# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base2.auth import (
    AuthBlueprint,
    AuthManager
)


@pytest.fixture
def auth_manager() -> AuthManager:
    return create_autospec(AuthManager, spec_set=True)


@pytest.fixture
def app(auth_manager: AuthManager) -> Flask:
    app_fixture = Flask(__name__)
    auth_bp = AuthBlueprint(auth_manager, '/auth')
    app_fixture.register_blueprint(auth_bp)
    return app_fixture


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
