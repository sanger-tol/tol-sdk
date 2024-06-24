# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Inc(BaseModel):
    __tablename__ = 'inc'

    id_indeed: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    string_column: Mapped[str] = mapped_column(nullable=True)

    @classmethod
    def get_id_column_name(cls):
        return 'id_indeed'
