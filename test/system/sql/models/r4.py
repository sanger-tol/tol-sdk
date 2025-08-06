# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r3 import R3


class R4(BaseModel):
    """
    to-many -> r3
    """

    __tablename__ = 'r4'

    id_r4: Mapped[str] = mapped_column(primary_key=True)

    le_r3s: Mapped[list[R3]] = relationship(
        back_populates='r4_mine'
    )

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_r4'
