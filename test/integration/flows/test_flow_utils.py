# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.flows import FlowUtils
from tol.sources.benchling import benchling
from tol.sources.portaldb import portaldb
from tol.sources.sts import sts


@pytest.fixture(scope='module')
def benchling_ds():
    return benchling()


class TestFlowUtils:
    def test_returns_worklist_when_found(self, benchling_ds):
        existing_name = 'ROUTINE tissue to prep for HiC'

        result = FlowUtils.get_worklist(bds=benchling_ds, worklist_name=existing_name)

        assert result is not None
        assert result.name == existing_name

    def test_returns_none_for_nonexistent_worklist(self, benchling_ds):
        result = FlowUtils.get_worklist(
            bds=benchling_ds,
            worklist_name='__nonexistent_worklist_name__'
        )

        assert result is None

    def test_returns_none_when_name_is_none(self, benchling_ds):
        result = FlowUtils.get_worklist(bds=benchling_ds, worklist_name=None)

        assert result is None

    def test_get_user_name_and_eln_api_key(self):
        portaldb_ds = portaldb()
        sts_ds = sts()
        portal_user_id = 1
        user_name, eln_api_key = FlowUtils.get_user_name_and_eln_api_key(
            portaldb_ds=portaldb_ds,
            sts_ds=sts_ds,
            portal_user_id=portal_user_id
        )
        assert user_name == 'Andrew Varley'
        assert eln_api_key is not None
