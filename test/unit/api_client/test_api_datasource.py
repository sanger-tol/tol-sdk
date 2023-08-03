# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client import ApiDataSource


class TestApiDataSource:
    def test_fake(self):
        ApiDataSource("","")

