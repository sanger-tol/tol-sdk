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


class R1(BaseModel):
    """
    to-one -> r2
    to-many -> r3
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

    users: Mapped[list['User']] = relationship(  # noqa F821
        back_populates='this_r1'
    )

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_override'
