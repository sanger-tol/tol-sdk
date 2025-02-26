# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

from .r6_to_r7 import R6toR7


class R7(BaseModel):

    __tablename__ = 'r7'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa

    joins_stuff: Mapped[list['R6toR7']] = relationship(
        back_populates='r7_rel'
    )
