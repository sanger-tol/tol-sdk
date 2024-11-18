# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

from flask import Blueprint

from tol.core import OperableDataSource
from tol.api_base2.misc import (
    CtxGetter,
    default_ctx_getter
)
from tol.api_client2.view import (
    DefaultView,
    View
)


ViewFactory = Callable[[], View]


def dashboard_blueprint(
    ds: OperableDataSource,

    admin_role: str = 'admin',
    ctx_getter: CtxGetter = default_ctx_getter,
    view_factory: ViewFactory = lambda: DefaultView()
) -> Blueprint:
    """
    A flask `Blueprint`
    """

    board_bp = Blueprint(
        'dashboard',
        __name__
    )

    return board_bp
