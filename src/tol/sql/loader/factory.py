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
    loader_instance: type[Model]
    data_source_config: type[Model]
    data_source_config_attribute: type[Model]
    data_source_config_relationship: type[Model]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """

        return iter(
            [
                self.data_source_config_relationship,
                self.data_source_config_attribute,
                self.data_source_config,
                self.loader_instance,
                self.loader,
                self.data_source_instance,
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
    class LoaderInstance(base_model_class):
        __tablename__ = 'loader_instance'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        # Frequency of loading
        frequency_weekly: Mapped[bool] = mapped_column(nullable=True)
        frequency_daily: Mapped[bool] = mapped_column(nullable=True)
        frequency_hourly: Mapped[bool] = mapped_column(nullable=True)
        frequency_quarter_hourly: Mapped[bool] = mapped_column(nullable=True)
        date_last_run: Mapped[datetime] = mapped_column(nullable=True)

        # Loader
        loader_id: Mapped[int] = mapped_column(
            ForeignKey('loader.id'),
            nullable=False
        )
        loader: Mapped['Loader'] = relationship(  # noqa F821
            back_populates='loader_instances',
            foreign_keys=[loader_id]
        )

        # Relationships
        source_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        source_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='source_loader_instances',
            foreign_keys=[source_data_source_instance_id]
        )

        destination_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        destination_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='destination_loader_instances',
            foreign_keys=[destination_data_source_instance_id]
        )

        ids_data_source_instance_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=True
        )
        ids_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='ids_loader_instances',
            foreign_keys=[ids_data_source_instance_id]
        )

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

        # For loading by IDs
        ids_object_type: Mapped[str] = mapped_column(nullable=True)
        ids_attribute: Mapped[str] = mapped_column(nullable=True)
        ids_object_filters: Mapped[dict] = mapped_column(JSONB, nullable=True)
        ids_sort_by: Mapped[str] = mapped_column(nullable=True)
        ids_attribute_in_source: Mapped[str] = mapped_column(nullable=True)

        loader_instances: Mapped[list['LoaderInstance']] = relationship(  # noqa F821
            back_populates='loader',
            foreign_keys=[LoaderInstance.loader_id]
        )

    class DataSourceInstance(base_model_class):
        __tablename__ = 'data_source_instance'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        name: Mapped[str] = mapped_column(nullable=False)
        builtin_name: Mapped[str] = mapped_column(nullable=False)
        kwargs: Mapped[dict] = mapped_column(JSONB, nullable=True)
        publish: Mapped[bool] = mapped_column(nullable=False, default=False)

        data_source_config_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_config.id'),
            nullable=False
        )
        data_source_config: Mapped['DataSourceConfig'] = relationship(  # noqa F821
            back_populates='data_source_instances',
            foreign_keys=[data_source_config_id]
        )

        source_loader_instances: Mapped[list['LoaderInstance']] = relationship(  # noqa F821
            back_populates='source_data_source_instance',
            foreign_keys=[LoaderInstance.source_data_source_instance_id]
        )
        destination_loader_instances: Mapped[list['LoaderInstance']] = relationship(  # noqa F821
            back_populates='destination_data_source_instance',
            foreign_keys=[LoaderInstance.destination_data_source_instance_id]
        )
        ids_loader_instances: Mapped[list['LoaderInstance']] = relationship(  # noqa F821
            back_populates='ids_data_source_instance',
            foreign_keys=[LoaderInstance.ids_data_source_instance_id]
        )

    class DataSourceConfigAttribute(base_model_class):
        __tablename__ = 'data_source_config_attribute'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003
        data_source_config_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_config.id'),
            nullable=False
        )
        data_source_config: Mapped['DataSourceConfig'] = relationship(  # noqa F821
            back_populates='data_source_config_attributes',
            foreign_keys=[data_source_config_id]
        )

        name: Mapped[str] = mapped_column(nullable=False)
        object_type: Mapped[str] = mapped_column(nullable=False)
        name: Mapped[str] = mapped_column(nullable=False)
        display_name: Mapped[str] = mapped_column(nullable=True)
        description: Mapped[str] = mapped_column(nullable=True)
        available_on_relationships: Mapped[bool] = mapped_column(nullable=False, default=True)
        is_authoritative: Mapped[bool] = mapped_column(nullable=False, default=False)
        source: Mapped[str] = mapped_column(nullable=True)
        runtime_definition: Mapped[str] = mapped_column(nullable=True)

    class DataSourceConfigRelationship(base_model_class):
        __tablename__ = 'data_source_config_relationship'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003
        object_type: Mapped[str] = mapped_column(nullable=False)
        name: Mapped[str] = mapped_column(nullable=False)
        foreign_object_type: Mapped[str] = mapped_column(nullable=False)
        foreign_name: Mapped[str] = mapped_column(nullable=False)

        data_source_config_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_config.id'),
            nullable=False
        )
        data_source_config: Mapped['DataSourceConfig'] = relationship(  # noqa F821
            back_populates='data_source_config_relationships',
            foreign_keys=[data_source_config_id]
        )

    class DataSourceConfig(base_model_class):
        __tablename__ = 'data_source_config'

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        name: Mapped[str] = mapped_column(nullable=False)
        description: Mapped[str] = mapped_column(nullable=False)

        data_source_instances: Mapped[list['DataSourceInstance']] = relationship(  # noqa F821
            back_populates='data_source_config',
            foreign_keys=[DataSourceInstance.data_source_config_id]
        )
        data_source_config_attributes: Mapped[list['DataSourceConfigAttribute']] = relationship(  # noqa F821
            back_populates='data_source_config',
            foreign_keys=[DataSourceConfigAttribute.data_source_config_id]
        )
        data_source_config_relationships: Mapped[list['DataSourceConfigRelationship']] = relationship(  # noqa F821
            back_populates='data_source_config',
            foreign_keys=[DataSourceConfigRelationship.data_source_config_id]
        )

    return LoaderModels(
        loader=Loader,
        data_source_instance=DataSourceInstance,
        loader_instance=LoaderInstance,
        data_source_config=DataSourceConfig,
        data_source_config_attribute=DataSourceConfigAttribute,
        data_source_config_relationship=DataSourceConfigRelationship
    )
