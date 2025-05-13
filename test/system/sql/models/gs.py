# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class GS(BaseModel):
    __tablename__ = 'gs'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    string_column: Mapped[str] = mapped_column(nullable=True)
    int_column: Mapped[int] = mapped_column(nullable=True)
    bool_column: Mapped[bool] = mapped_column(nullable=True)
