# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

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


ALL_MODELS = (
    Root,
)
