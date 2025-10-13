# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    ForeignKey,
    JSON,
    event,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from tol.sql import model_base


TEST_OBJECT_TYPES = (
    'root',
    'related',
)


ModelBase = model_base()  # noqa


class Root(ModelBase):
    """
    The Root `ModelBase` child.

    Has `object_type="root"`
    """

    __tablename__ = 'root'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    str_column: Mapped[str] = mapped_column(nullable=True)
    int_column: Mapped[int] = mapped_column(nullable=True)
    datetime_column: Mapped[datetime] = mapped_column(nullable=True)
    bool_column: Mapped[bool] = mapped_column(nullable=True)
    list_column: Mapped[list] = mapped_column(
        type_=JSON,
        nullable=True
    )
    dict_column: Mapped[dict] = mapped_column(
        type_=JSON,
        nullable=True
    )
    runtime_column: Mapped[bool] = mapped_column(nullable=True)

    related_fkey: Mapped[str] = mapped_column(
        ForeignKey('related.id'),
        nullable=True
    )
    related_object: Mapped[Related] = relationship(
        back_populates='my_root',
        foreign_keys=[related_fkey]
    )

    another_fkey: Mapped[str] = mapped_column(
        ForeignKey('related.id'),
        nullable=True
    )
    another_related: Mapped[Related] = relationship(
        back_populates='yet_still_root',
        foreign_keys=[another_fkey]
    )


@event.listens_for(Root.bool_column, 'set', retval=False)
def update_runtime_column(
    target: Root,
    value: bool | None,
    __old: bool | None,
    __init: Any
):
    target.runtime_column = not value
    return value


class Related(ModelBase):
    """
    The "related" `ModelBase` child.

    Has `object_type` related
    """

    __tablename__ = 'related'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

    str_column: Mapped[str] = mapped_column(nullable=True)
    int_column: Mapped[int] = mapped_column(nullable=True)
    datetime_column: Mapped[datetime] = mapped_column(nullable=True)
    bool_column: Mapped[bool] = mapped_column(nullable=True)
    list_column: Mapped[list] = mapped_column(
        type_=JSON,
        nullable=True
    )

    my_root: Mapped[list[Root]] = relationship(
        back_populates='related_object',
        foreign_keys=[Root.related_fkey]
    )

    yet_still_root: Mapped[list[Root]] = relationship(
        back_populates='another_related',
        foreign_keys=[Root.another_fkey]
    )


class Inc(ModelBase):
    __tablename__ = 'inc'

    id_indeed: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    string_column: Mapped[str] = mapped_column(nullable=True)

    @classmethod
    def get_id_column_name(cls):
        return 'id_indeed'


ALL_MODELS = (
    Related,
    Root,
    Inc
)
