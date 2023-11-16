# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class C(BaseModel.Log):
    __tablename__ = 'c'

    id_override: Mapped[str] = mapped_column(primary_key=True)
    string_column: Mapped[str] = mapped_column(nullable=True)

    @classmethod
    def get_id_column_name(cls):
        return 'id_override'
