# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.misc import AuthContext
from tol.api_base2.misc.auth_context import (
    NotAuthenticatedError
)


class TestAuthContext:
    def test_get_and_set(self):
        """
        get and set works for `user_id` and `roles`
        """

        ctx = AuthContext()

        assert ctx.authenticated is False

        with pytest.raises(NotAuthenticatedError):
            ctx.user_id

        with pytest.raises(NotAuthenticatedError):
            ctx.roles

        ctx.user_id = 'test_id'

        assert ctx.user_id == 'test_id'
        assert ctx.roles == []

        ctx.roles = ['hype', 'train']

        assert ctx.roles == ['hype', 'train']
