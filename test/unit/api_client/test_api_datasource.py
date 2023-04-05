# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .mock import api_ds, mock_upsert


class TestApiDataSource:
    @mock_upsert()
    def test_no_upsert_no_call(self, upsert_mock):
        with api_ds.session():
            pass
        assert upsert_mock.call_count == 0
