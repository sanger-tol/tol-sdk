# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.api_base2.auth import OidcConfig
from tol.sql.auth import db_auth_blueprint
from tol.sql.board import create_board_models

from .a import A
from .b import B
from .base import BaseModel
from .c import C
from .ext import ExtDefault, ExtOverride
from .inc import Inc
from .r1 import R1
from .r2 import R2
from .r3 import R3
from .r4 import R4
from .r5 import R5
from .user_mixin import TestUserMixin  # noqa F401


OIDC_CONFIG = OidcConfig(
    auth_url='http://local.lan/authorize',
    user_info_url='http://local.lan/userinfo',
    token_url='http://local.lan/token',
    revoke_url='http://local.lan/revoke',
    client_id='a fun ID',
    client_secret='bubbles',
    redirect_uri='http://other.lan/callback'
)


board_models = create_board_models(BaseModel)


user_mixin = type(
    '',
    (
        TestUserMixin,
        board_models._user_mixin
    ),
    {}
)


auth_bp = db_auth_blueprint(
    BaseModel,
    os.environ['DB_URI'],
    oidc_config_factory=lambda: OIDC_CONFIG,
    user_mixin_class=user_mixin,
    oidc_id_column_name='changed_lol',
    oidc_ext_mapping={
        'do_not_forget_me': 'extra_oidc_field',
        'me_neither': 'extra_oidc_int'
    }
)


delete_models_list = [
    A,
    B,
    C,
    Inc,
    R3,  # must come before R1, as it points to it
    R4,  # must come before R3, as it points to it
    R1,
    R5,
    R2,
    ExtDefault,
    ExtOverride,
    board_models.component_zone,
    board_models.zone_view,
    board_models.view_board,
    board_models.component,
    board_models.zone,
    board_models.view,
    board_models.board,
    auth_bp.models.user_class
]


create_models_list = list(reversed(delete_models_list))
