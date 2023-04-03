# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .mock import assert_upsert_body, mock_upsert


class TestApiDataSource:
    @mock_upsert
    def test_upsert_calls_unified_endpoint(self):
        assert_upsert_body({})
