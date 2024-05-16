# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r2 import R2
    from .r3 import R3
    from .r5 import R5


class R1(BaseModel):
    """
    to-one -> r2
    to-many -> r3
    to-one -> r4
    """

    __tablename__ = 'r1'

    id_override: Mapped[str] = mapped_column(primary_key=True)

    r2_foreign_key: Mapped[str] = mapped_column(
        ForeignKey('r2.id'),
        nullable=True
    )
    r2_d2: Mapped['R2'] = relationship(
        back_populates='mine_r1s'
    )

    r3_plz: Mapped[List['R3']] = relationship(
        back_populates='funny_r1'
    )

    r5_foreign_key: Mapped[str] = mapped_column(
        ForeignKey('r5.id'),
        nullable=True
    )
    this_lovely_r5: Mapped['R5'] = relationship(
        back_populates='no_more_r1s'
    )

    users: Mapped[list['User']] = relationship(  # noqa F821
        back_populates='this_r1'
    )

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_override'
