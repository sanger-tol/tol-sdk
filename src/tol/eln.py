# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling


ELN_API_LOCATION = os.environ['ELN_API_LOCATION']
FLOWS_ELN_API_KEY = os.environ["FLOWS_ELN_API_KEY"]


def get_benchling_instance():
    return Benchling(
        url=ELN_API_LOCATION,
        auth_method=ApiKeyAuth(FLOWS_ELN_API_KEY)
    )
