# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship
)

from ..model import Model


@dataclass(frozen=True, kw_only=True)
class StandardModels(IterableABC[type[Model]]):
    """
    Contains the needed models for dynamic, user-configurable
    dashboards.

    Additionally contains `_user_mixin`, from which developers
    should inherit their `User` class from `tol.sql.auth`.
    """

    loader: type[Model]
    data_source_instance: type[Model]
    loader_instance: type[Model]
    data_source_config: type[Model]
    data_source_config_attribute: type[Model]
    data_source_config_relationship: type[Model]
    data_source_config_summary: type[Model]
    component: type[Model]
    component_zone: type[Model]
    zone: type[Model]
    zone_view: type[Model]
    view: type[Model]
    view_board: type[Model]
    board: type[Model]

    _user_mixin: type[Any]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """

        return iter(
            [
                self.component_zone,
                self.component,
                self.zone_view,
                self.zone,
                self.view_board,
                self.view,
                self.board,
                self.data_source_config_summary,
                self.data_source_config_relationship,
                self.data_source_config_attribute,
                self.loader_instance,
                self.data_source_instance,
                self.data_source_config,
                self.loader
            ]
        )


def create_standard_models(
    base_model_class: type[Model],
    user_model_class_name: str = 'User',
    user_table_name: str = 'user'
) -> StandardModels:
    """
    Creates all needed models (and joining tables) for
    user-configurable dashboards.

    Returns a `StandardModels` instance that functions like an
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
        source_data_source_instance_id: Mapped[str] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        source_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='source_loader_instances',
            foreign_keys=[source_data_source_instance_id]
        )

        destination_data_source_instance_id: Mapped[str] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        destination_data_source_instance: Mapped['DataSourceInstance'] = relationship(  # noqa F821
            back_populates='destination_loader_instances',
            foreign_keys=[destination_data_source_instance_id]
        )

        ids_data_source_instance_id: Mapped[str] = mapped_column(
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

    class Component(base_model_class):
        __tablename__ = 'component'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
        )

        title: Mapped[str] = mapped_column(nullable=False)
        object_type: Mapped[str] = mapped_column(nullable=False)
        component_type: Mapped[str] = mapped_column(nullable=False)
        widget_type: Mapped[str] = mapped_column(nullable=False)
        config = mapped_column(type_=JSONB(), nullable=False)
        filter = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )
        filter_pass_through: Mapped[bool] = mapped_column(nullable=False)

        user_id: Mapped[int] = mapped_column(
            ForeignKey(f'{user_table_name}.id'),
            nullable=False
        )
        user = relationship(
            user_model_class_name,
            back_populates='components',
            foreign_keys=[user_id]
        )

        data_source_instance_id: Mapped[str] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        data_source_instance = relationship(
            'DataSourceInstance',
            back_populates='components',
            foreign_keys=[data_source_instance_id]
        )

        component_zones: Mapped[list[ComponentZone]] = relationship(
            back_populates='component'
        )

    class ComponentZone(base_model_class):
        __tablename__ = 'component_zone'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True
        )

        order: Mapped[int] = mapped_column(nullable=False)

        component_id: Mapped[str] = mapped_column(
            ForeignKey('component.id'),
            nullable=False
        )
        component = relationship(
            'Component',
            back_populates='component_zones',
            foreign_keys=[component_id]
        )

        zone_id: Mapped[str] = mapped_column(
            ForeignKey('zone.id'),
            nullable=False
        )
        zone = relationship(
            'Zone',
            back_populates='component_zones',
            foreign_keys=[zone_id]
        )

    class Zone(base_model_class):
        __tablename__ = 'zone'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
        )

        title: Mapped[str] = mapped_column(nullable=False)
        object_type: Mapped[str] = mapped_column(nullable=False)
        filter = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )

        component_zones: Mapped[list[ComponentZone]] = relationship(
            back_populates='zone'
        )

        zone_views: Mapped[list[ZoneView]] = relationship(
            back_populates='zone'
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey(f'{user_table_name}.id'),
            nullable=False
        )
        user = relationship(
            user_model_class_name,
            back_populates='zones',
            foreign_keys=[user_id]
        )

        data_source_instance_id: Mapped[str] = mapped_column(
            ForeignKey('data_source_instance.id'),
            nullable=False
        )
        data_source_instance = relationship(
            'DataSourceInstance',
            back_populates='zones',
            foreign_keys=[data_source_instance_id]
        )

    class ZoneView(base_model_class):
        __tablename__ = 'zone_view'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True
        )

        order: Mapped[int] = mapped_column(nullable=False)

        zone_id: Mapped[str] = mapped_column(
            ForeignKey('zone.id'),
            nullable=False
        )
        zone = relationship(
            'Zone',
            back_populates='zone_views',
            foreign_keys=[zone_id]
        )

        view_id: Mapped[str] = mapped_column(
            ForeignKey('view.id'),
            nullable=False
        )
        view = relationship(
            'View',
            back_populates='zone_views',
            foreign_keys=[view_id]
        )

    class View(base_model_class):
        __tablename__ = 'view'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
        )

        title: Mapped[str] = mapped_column(nullable=False)
        filter = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )

        zone_views: Mapped[list[ZoneView]] = relationship(
            back_populates='view'
        )

        view_boards: Mapped[list[ViewBoard]] = relationship(
            back_populates='view'
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey(f'{user_table_name}.id'),
            nullable=False
        )
        user = relationship(
            user_model_class_name,
            back_populates='views',
            foreign_keys=[user_id]
        )

    class ViewBoard(base_model_class):
        __tablename__ = 'view_board'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True
        )

        order: Mapped[int] = mapped_column(nullable=False)

        view_id: Mapped[str] = mapped_column(
            ForeignKey('view.id'),
            nullable=False
        )
        view = relationship(
            'View',
            back_populates='view_boards',
            foreign_keys=[view_id]
        )

        board_id: Mapped[str] = mapped_column(
            ForeignKey('board.id'),
            nullable=False
        )
        board = relationship(
            'Board',
            back_populates='view_boards',
            foreign_keys=[board_id]
        )

    class Board(base_model_class):
        __tablename__ = 'board'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
        )

        title: Mapped[str] = mapped_column(nullable=False)
        filter = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )

        view_boards: Mapped[list[ViewBoard]] = relationship(
            back_populates='board'
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey(f'{user_table_name}.id'),
            nullable=False
        )
        user = relationship(
            user_model_class_name,
            back_populates='boards',
            foreign_keys=[user_id]
        )

    class DataSourceInstance(base_model_class):
        __tablename__ = 'data_source_instance'

        id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003

        builtin_name: Mapped[str] = mapped_column(nullable=False)
        kwargs: Mapped[dict] = mapped_column(JSONB, nullable=True)
        publish: Mapped[bool] = mapped_column(nullable=False, default=False)
        ui_api_details: Mapped[dict] = mapped_column(JSONB, nullable=True)

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
        components: Mapped[list['Component']] = relationship(  # noqa F821
            back_populates='data_source_instance',
            foreign_keys=[Component.data_source_instance_id]
        )
        zones: Mapped[list['Zone']] = relationship(  # noqa F821
            back_populates='data_source_instance',
            foreign_keys=[Zone.data_source_instance_id]
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
        display_name: Mapped[str] = mapped_column(nullable=True)
        description: Mapped[str] = mapped_column(nullable=True)
        available_on_relationships: Mapped[bool] = mapped_column(nullable=False, default=True)
        is_authoritative: Mapped[bool] = mapped_column(nullable=False, default=False)
        source: Mapped[str] = mapped_column(nullable=True)
        runtime_definition: Mapped[dict] = mapped_column(JSONB, nullable=True)

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

    class DataSourceConfigSummary(base_model_class):
        __tablename__ = 'data_source_config_summary'

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

        data_source_config_id: Mapped[int] = mapped_column(
            ForeignKey('data_source_config.id'),
            nullable=False
        )

        data_source_config: Mapped['DataSourceConfig'] = relationship(  # noqa F821
            back_populates='data_source_config_summaries',
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
        data_source_config_summaries: Mapped[list['DataSourceConfigSummary']] = relationship(
            back_populates='data_source_config',
            foreign_keys=[DataSourceConfigSummary.data_source_config_id]
        )

    class _UserMixin:

        @declared_attr
        def components(self) -> Mapped[list[Component]]:
            return relationship(
                back_populates='user'
            )

        @declared_attr
        def zones(self) -> Mapped[list[Zone]]:
            return relationship(
                back_populates='user'
            )

        @declared_attr
        def views(self) -> Mapped[list[View]]:
            return relationship(
                back_populates='user'
            )

        @declared_attr
        def boards(self) -> Mapped[list[Board]]:
            return relationship(
                back_populates='user'
            )

    return StandardModels(
        loader=Loader,
        data_source_instance=DataSourceInstance,
        loader_instance=LoaderInstance,
        data_source_config=DataSourceConfig,
        data_source_config_attribute=DataSourceConfigAttribute,
        data_source_config_relationship=DataSourceConfigRelationship,
        data_source_config_summary=DataSourceConfigSummary,
        component=Component,
        component_zone=ComponentZone,
        zone=Zone,
        zone_view=ZoneView,
        view=View,
        view_board=ViewBoard,
        board=Board,
        _user_mixin=_UserMixin
    )
