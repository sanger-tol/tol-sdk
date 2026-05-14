# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.flows import FlowUtils
from tol.sources.portaldb import portaldb
from tol.sources.sts import sts


class TestFlowUtils:
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
