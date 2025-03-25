# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from typing import Iterator

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from ..model import Model


@dataclass(frozen=True, kw_only=True)
class SummaryModels(IterableABC[type[Model]]):
    """
    Contains the needed models for summarys.

    """

    summary: type[Model]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """

        return iter(
            [
                self.summary
            ]
        )


def create_summary_models(
    base_model_class: type[Model]
) -> SummaryModels:
    """
    Creates all needed models (and joining tables) for
    summaries.

    Returns a `SummaryModels` instance that functions like an
    `Iterable`.
    """

    class Summary(base_model_class):
        __tablename__ = 'summary'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        source_object_type: Mapped[str] = mapped_column(nullable=False)
        destination_object_type: Mapped[str] = mapped_column(nullable=True)

        object_filters: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default={}
        )

        group_by: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default=[]
        )

        stats_fields: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default=[]
        )

        stats: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default=[]
        )

        prefix: Mapped[str] = mapped_column(
            nullable=False,
            default=''
        )

    return SummaryModels(
        summary=Summary,
    )
