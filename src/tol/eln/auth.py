# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling

ELN_URL = os.getenv('ELN_URL')
ELN_API_KEY = os.getenv('ELN_API_KEY')


def get_benchling_instance():
    return Benchling(
        url=ELN_URL,
        auth_method=ApiKeyAuth(ELN_API_KEY)
    )
