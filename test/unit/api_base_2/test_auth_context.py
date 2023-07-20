# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base2.misc import AuthContext


class TestAuthContext:
    def test_get_and_set(self):
        """get and set works for user_id"""

        ctx = AuthContext()

        assert ctx.user_id is None

        ctx.user_id = 'test_id'
        assert ctx.user_id == 'test_id'
