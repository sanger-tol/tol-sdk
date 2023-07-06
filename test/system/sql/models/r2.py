# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r1 import R1


class R2(BaseModel):
    """
    to-many -> r1
    """

    __tablename__ = 'r2'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    mine_r1s: Mapped[List['R1']] = relationship(
        back_populates='r2_d2'
    )
