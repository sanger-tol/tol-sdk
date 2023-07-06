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


class R3(BaseModel):
    """
    to-one -> r1
    """

    __tablename__ = 'r3'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    ur_r1_id: Mapped[str] = mapped_column(
        ForeignKey('r1.id_override')
    )

    funny_r1: Mapped['R1'] = relationship(
        back_populates='r3_plz'
    )
