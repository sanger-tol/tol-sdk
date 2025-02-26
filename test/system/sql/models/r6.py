# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

from .r1_to_r6 import R1ToR6


class R6(BaseModel):

    __tablename__ = 'r6'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa

    joins_stuff: Mapped[list['R1ToR6']] = relationship(
        back_populates='r6_rel'
    )
