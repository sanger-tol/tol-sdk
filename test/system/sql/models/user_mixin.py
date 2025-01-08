# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship
)

from .board import board_user_mixin

if typing.TYPE_CHECKING:
    from .r1 import R1


class TestUserMixin(board_user_mixin):
    """
    Augments user with:

    - FK to `R1` to demonstrate `UserMixin`
    - an extra field for OIDC
    """

    @declared_attr
    def extra_oidc_field(cls) -> Mapped[str]:  # noqa N805
        return mapped_column(nullable=True)

    @declared_attr
    def extra_oidc_int(cls) -> Mapped[int]:  # noqa N805
        return mapped_column(nullable=True)

    @declared_attr
    def r1_id(cls) -> Mapped[str]:  # noqa N805
        return mapped_column(
            ForeignKey('r1.id_override'),
            nullable=True
        )

    @declared_attr
    def this_r1(cls) -> Mapped[R1]:  # noqa N805
        return relationship(
            foreign_keys=[cls.r1_id]
        )
