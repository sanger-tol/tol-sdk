# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class A(BaseModel):
    __tablename__ = 'a'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    string_column: Mapped[str] = mapped_column(nullable=True)
