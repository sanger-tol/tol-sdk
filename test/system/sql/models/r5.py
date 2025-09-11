# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if typing.TYPE_CHECKING:
    from .r1 import R1


class R5(BaseModel):
    """
    to-many -> r1
    """

    __tablename__ = 'r5'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa

    funny_word: Mapped[str] = mapped_column()

    no_more_r1s: Mapped[list[R1]] = relationship(
        back_populates='this_lovely_r5'
    )
