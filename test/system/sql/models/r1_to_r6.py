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
    from .r6 import R6


class R1ToR6(BaseModel):
    """
    Joining table between R1 and R6
    """

    __tablename__ = 'r1_r6'

    r1_id: Mapped[str] = mapped_column(
        ForeignKey('r1.id_override'),
        nullable=False,
        primary_key=True
    )
    r1_rel: Mapped['R1'] = relationship(
        back_populates='joins_stuff'
    )

    r6_id: Mapped[str] = mapped_column(
        ForeignKey('r6.id'),
        nullable=False,
        primary_key=True
    )
    r6_rel: Mapped['R6'] = relationship(
        back_populates='joins_stuff'
    )
