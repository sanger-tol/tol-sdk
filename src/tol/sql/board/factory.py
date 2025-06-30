# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
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
class BoardModels(IterableABC[type[Model]]):
    """
    Contains the needed models for dynamic, user-configurable
    dashboards.

    Additionally contains `_user_mixin`, from which developers
    should inherit their `User` class from `tol.sql.auth`.
    """

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
                self.board
            ]
        )


def create_board_models(
    base_model_class: type[Model],
    user_model_class_name: str = 'User',
    user_table_name: str = 'user'
) -> BoardModels:
    """
    Creates all needed models (and joining tables) for
    user-configurable dashboards.

    Returns a `BoardModels` instance that functions like an
    `Iterable`.
    """

    class Component(base_model_class):
        __tablename__ = 'component'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
        )

        title: Mapped[str] = mapped_column(nullable=False)
        object_type: Mapped[str] = mapped_column(nullable=False)
        datasource = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )
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
        datasource = mapped_column(  # noqa A003
            type_=JSONB(),
            nullable=False,
            default={},
            server_default='{}'  # noqa P103
        )
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

    return BoardModels(
        component=Component,
        component_zone=ComponentZone,
        zone=Zone,
        zone_view=ZoneView,
        view=View,
        view_board=ViewBoard,
        board=Board,
        _user_mixin=_UserMixin
    )
