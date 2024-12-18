# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

from tol.api_base2.auth import ForbiddenError
from tol.api_base2.misc import AuthContext
from tol.api_base2.misc.auth_context import (
    NotAuthenticatedError
)


class TestActionRole:
    """Access requires correct role."""

    def test__no_auth(
        self,
        client: FlaskClient
    ):

        with pytest.raises(NotAuthenticatedError):
            client.post('/run-action')

    def test__no_roles(
        self,
        client: FlaskClient,
        ctx: AuthContext
    ):

        ctx.user_id = 101
        ctx.roles = []

        with pytest.raises(ForbiddenError):
            client.post('/run-action')

    def test__bad_roles(
        self,
        client: FlaskClient,
        ctx: AuthContext
    ):

        ctx.user_id = 101
        ctx.roles = list('abc')

        with pytest.raises(ForbiddenError):
            client.post('/run-action')
