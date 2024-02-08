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

if typing.TYPE_CHECKING:
    from .r1 import R1


class TestUserMixin:
    """Points at `R1` to demonstrate `UserMixin`"""

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
