# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from tol.core import DataSource, core_data_object


class TestFetch:
    """No superfluous fetches"""

    def test_empty_dict(self):
        """
        `_to_one_objects[__k] == {}` -> no fetch
        """

    def test_none(self):
        """
        `_to_one_objects[__k] is None` -> no fetch
        """
