# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship
)

from ..model import Model


@dataclass(frozen=True, kw_only=True)
class ActionModels(IterableABC[type[Model]]):
    """
    Contains the needed models for actions.

    Additionally contains `_user_mixin`, from which developers
    should inherit their `User` class from `tol.sql.auth`.
    """

    action: type[Model]
    user_action: type[Model]

    _user_mixin: type[Any]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """

        return iter(
            [
                self.user_action,
                self.action
            ]
        )


def create_action_models(
    base_model_class: type[Model]
) -> ActionModels:
    """
    Creates all needed models (and joining tables) for
    actions.

    Returns a `ActionModels` instance that functions like an
    `Iterable`.
    """

    class Action(base_model_class):
        __tablename__ = 'action'

        __table_args__ = (
            UniqueConstraint('name', 'object_type'),
        )

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        name: Mapped[str] = mapped_column(nullable=False)
        object_type: Mapped[str] = mapped_column(nullable=False)

        flow_name: Mapped[str] = mapped_column(nullable=False)
        params: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default={}
        )

        user_actions: Mapped[list['UserAction']] = relationship(  # noqa F821
            back_populates='action'
        )

    class UserAction(base_model_class):
        __tablename__ = 'user_action'

        __table_args__ = (
            CheckConstraint('NOT(ids IS NULL AND filters IS NULL)'),
        )

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # noqa A003

        created_at: Mapped[datetime] = mapped_column(
            nullable=False,
            default=datetime.now
        )
        params: Mapped[dict] = mapped_column(
            JSONB,
            nullable=False,
            default={}
        )

        ids: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
        filters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)

        action_id: Mapped[int] = mapped_column(
            ForeignKey('action.id'),
            nullable=False
        )
        action: Mapped['Action'] = relationship(  # noqa F821
            back_populates='user_actions',
            foreign_keys=[action_id]
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey('user.id'),
            nullable=False
        )
        user: Mapped['User'] = relationship(  # noqa F821
            back_populates='user_actions',
            foreign_keys=[user_id]
        )

    class _UserMixin:

        @declared_attr
        def user_actions(self) -> Mapped[list[UserAction]]:
            return relationship(
                back_populates='user'
            )

    return ActionModels(
        action=Action,
        user_action=UserAction,
        _user_mixin=_UserMixin
    )
