# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.api_client.client import DefaultApiClient


class TestDefaultApiClient:
    """
    Tests `DefaultApiClient`, with outward calls mocked using
    `responses`.
    """
