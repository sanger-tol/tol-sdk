# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from tol.sql import ext

from .base import BaseModel


@ext
class ExtDefault(BaseModel):

    __tablename__ = 'ext_default'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    string_column: Mapped[str] = mapped_column(nullable=True)

    ext: Mapped[dict] = mapped_column(nullable=True)


@ext(target='ext_lol')
class ExtOverride(BaseModel):
    """
    Has a different ext `column_name` and a nullable JSON type.
    """

    __tablename__ = 'ext_override'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    string_column: Mapped[str] = mapped_column(nullable=True)

    ext_lol: Mapped[dict[str, Any]] = mapped_column(nullable=True)
