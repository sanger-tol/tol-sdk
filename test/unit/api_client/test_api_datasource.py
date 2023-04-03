# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .mock import mock_upsert


class TestApiDataSource:
    @mock_upsert({})
    def test_upsert_calls_unified_endpoint(self, upsert_mock):
        print(upsert_mock)
        assert False
