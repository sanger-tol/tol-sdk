# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from sqlalchemy import (
    ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from ..model import Model


@dataclass(frozen=True, kw_only=True)
class LoaderModels(IterableABC[type[Model]]):
    """
    Contains the needed models for loaders.

    """

    data_source_instance: type[Model]
    loader: type[Model]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """

        return iter(
            [
                self.loader,
                self.data_source_instance
            ]
        )


def create_loader_models(
    base_model_class: type[Model]
) -> LoaderModels:
    """
    Creates all needed models (and joining tables) for
    loaders.

    Returns a `LoaderModels` instance that functions like an
    `Iterable`.
    """

    class Loader(base_model_class):
        __tablename__ = 'loader'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        source_object_type: Mapped[str] = mapped_column(nullable=False)
        destination_object_type: Mapped[str] = mapped_column(nullable=False)

        object_filters: Mapped[dict] = mapped_column(
            JSONB,
            nullable=True
        )

        prefix: Mapped[str] = mapped_column(nullable=False, default='')
        convert_class: Mapped[str] = mapped_column(nullable=True)
        candidate_key: Mapped[dict] = mapped_column(JSONB, nullable=True)
        date_last_run: Mapped[datetime] = mapped_column(nullable=True)

        # Frequency of loading
        frequency_weekly: Mapped[bool] = mapped_column(nullable=True)
        frequency_daily: Mapped[bool] = mapped_column(nullable=True)
        frequency_hourly: Mapped[bool] = mapped_column(nullable=True)
        frequency_quarter_hourly: Mapped[bool] = mapped_column(nullable=True)

        # For loading by IDs
        ids_object_type: Mapped[str] = mapped_column(nullable=True)
        ids_attribute: Mapped[str] = mapped_column(nullable=True)
        ids_object_filters: Mapped[dict] = mapped_column(JSONB, nullable=True)
        ids_sort_by: Mapped[str] = mapped_column(nullable=True)
        ids_attribute_in_source: Mapped[str] = mapped_column(nullable=True)

        # Rerlationships
        source_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        source_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='source_loaders',
            foreign_keys=[source_data_source_instance_id]
        )

        destination_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        destination_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='destination_loaders',
            foreign_keys=[destination_data_source_instance_id]
        )
        ids_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=True
        )
        ids_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='ids_loaders',
            foreign_keys=[ids_data_source_instance_id]
        )

    class DataSourceInstance(base_model_class):
        __tablename__ = 'data_source_instance'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        name: Mapped[str] = mapped_column(nullable=False)
        builtin_name: Mapped[str] = mapped_column(nullable=False)

        source_loaders: Mapped[list['Loader']] = relationship(  # noqa F821
            back_populates='source_data_source_instance',
            foreign_keys=[Loader.source_data_source_instance_id]
        )
        destination_loaders: Mapped[list['Loader']] = relationship(  # noqa F821
            back_populates='destination_data_source_instance',
            foreign_keys=[Loader.destination_data_source_instance_id]
        )
        ids_loaders: Mapped[list['Loader']] = relationship(  # noqa F821
            back_populates='ids_data_source_instance',
            foreign_keys=[Loader.ids_data_source_instance_id]
        )

    return LoaderModels(
        loader=Loader,
        data_source_instance=DataSourceInstance
    )
