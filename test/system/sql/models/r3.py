# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r1 import R1
    from .r4 import R4


class R3(BaseModel):
    """
    to-one -> r1
    """

    __tablename__ = 'r3'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    another_string: Mapped[str] = mapped_column(nullable=True)

    ur_r1_id: Mapped[str] = mapped_column(
        ForeignKey('r1.id_override'),
        nullable=True,
    )

    funny_r1: Mapped['R1'] = relationship(
        back_populates='r3_plz'
    )

    r4_foreign_key: Mapped[str] = mapped_column(
        ForeignKey('r4.id_r4'),
        nullable=True
    )
    r4_mine: Mapped['R4'] = relationship(
        back_populates='le_r3s'
    )
