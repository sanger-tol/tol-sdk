# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

from tol.log import Logger


class TestLogger:
    """Tests the logger class"""

    def test_none_user_id(self):
        """got `user_id` is `None` -> don't log"""

    def test_set_user_id(self):
        """`user_id` is set and not `None` -> should log"""
