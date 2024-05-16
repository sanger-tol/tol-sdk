# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class B(BaseModel):
    __tablename__ = 'b'

    id_override: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    int_column: Mapped[int] = mapped_column()
    another_string: Mapped[str] = mapped_column(nullable=True)

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_override'
