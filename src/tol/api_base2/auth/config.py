# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OidcConfig:
    """Stores OIDC-related config."""

    auth_url: str
    """The URL using which to Login"""

    user_info_url: str
    """The User Info URL"""

    token_url: str
    """The URL for getting tokens"""

    revoke_url: str
    """The URL for revoking tokens"""

    client_id: str
    """The ID of the client"""

    client_secret: str
    """The secret of the client"""

    redirect_uri: str
    """The URI to which to redirect after auth"""


def env_oidc_config() -> OidcConfig:
    """
    Populates an `OidcConfig` using environment
    variables.
    """

    return OidcConfig(
        auth_url=os.environ['OIDC_AUTH_URL'],
        user_info_url=os.environ['OIDC_USER_INFO_URL'],
        token_url=os.environ['OIDC_TOKEN_URL'],
        revoke_url=os.environ['OIDC_REVOKE_TOKEN_URL'],
        client_id=os.environ['OIDC_CLIENT_ID'],
        client_secret=os.environ['OIDC_CLIENT_SECRET'],
        redirect_uri=os.environ['OIDC_REDIRECT_URI']
    )
