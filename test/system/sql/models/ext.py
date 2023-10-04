# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from tol.sql import ext

from .base import BaseModel


@ext
class ExtDefault(BaseModel):

    __tablename__ = 'ext_default'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    string_column: Mapped[str] = mapped_column(nullable=True)

    # adding this in twice is really hacky :( but sadly necessary!
    ext = Column(JSON)


@ext(
    column_name='ext_lol',
    column_factory=lambda: Column(JSONB, nullable=True)
)
class ExtOverride(BaseModel):
    """
    Has a different ext `column_name` and a nullable JSON type.
    """

    __tablename__ = 'ext_override'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    string_column: Mapped[str] = mapped_column(nullable=True)

    # adding this in twice is really hacky :( but sadly necessary!
    ext_lol = Column(JSONB, nullable=True)
