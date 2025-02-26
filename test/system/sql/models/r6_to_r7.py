# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r7 import R7
    from .r6 import R6


class R6toR7(BaseModel):
    """
    Joining table between R1 and R6
    """

    __tablename__ = 'r6_r7'

    r7_id: Mapped[str] = mapped_column(
        ForeignKey('r7.id'),
        nullable=False,
        primary_key=True
    )
    r7_rel: Mapped['R7'] = relationship(
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
