# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterator, List

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    declared_attr,
    mapped_column,
    relationship
)

from ..model import Model


@dataclass(frozen=True, kw_only=True)
class PipelineStepModels(IterableABC[type[Model]]):
    """
    Contains the needed models for users to run steps
    in validation pipelines.

    Additionally contains `_user_mixin`, from which developers
    should inherit their `User` class from `tol.sql.auth`.
    """

    pipeline: type[Model]
    pipeline_step: type[Model]
    upload: type[Model]

    _user_mixin: type[Any]

    def __iter__(self) -> Iterator[type[Model]]:
        """
        Returns in order they should be deleted
        """
        return iter(
            [
                self.upload,
                self.pipeline_step,
                self.pipeline,
            ]
        )


def create_pipeline_step_models(
    base_model_class: type[Model]
) -> PipelineStepModels:
    """
    Creates all needed models (and joining tables) for
    validation pipelines.

    Returns a `PipelineStepModels` instance that functions like an
    `Iterable`.
    """

    class Pipeline(base_model_class):
        __tablename__ = 'pipeline'

        id: Mapped[int] = mapped_column( # noqa A003
            primary_key=True,
            autoincrement=True
        )

        name: Mapped[str] = mapped_column(
            nullable=False,
            unique=True,
        )

        config: Mapped[dict[str, Any]] = mapped_column(
            nullable=False,
            default={}
        )

        uploads: Mapped[list[Upload]] = relationship(
            'Upload',
            back_populates='pipeline'
        )

        steps: Mapped[list[PipelineStep]] = relationship(
            'PipelineStep',
            back_populates='pipeline'
        )

    class PipelineStep(base_model_class):
        __tablename__ = 'pipeline_steps'
        __table_args__ = (
            UniqueConstraint(
                'pipeline_id',
                'stage',
                'step_order',
                name='uq_pipeline_step_stage_order'
            ),
        )

        id: Mapped[int] = mapped_column( # noqa A003
            primary_key=True,
            autoincrement=True
        )

        pipeline_id: Mapped[int] = mapped_column(
            ForeignKey('pipeline.id')
        )

        step_name: Mapped[str] = mapped_column(
            nullable=False
        )

        stage: Mapped[int] = mapped_column(
            nullable=False
        )

        step_order: Mapped[int] = mapped_column(
            nullable=False
        )

        config: Mapped[dict[str, Any]] = mapped_column(
            JSONB,
            nullable=False,
            default={}
        )

        pipeline: Mapped[Pipeline] = relationship(
            'Pipeline',
            back_populates='steps'
        )

    class Upload(base_model_class):
        __tablename__ = 'upload'

        id: Mapped[int] = mapped_column( # noqa A003
            primary_key=True,
            autoincrement=True
        )

        s3_url: Mapped[str] = mapped_column(nullable=False,)
        s3_filename: Mapped[str] = mapped_column(nullable=False)
        spreadsheet_config: Mapped[str] = mapped_column(nullable=True)

        user_id: Mapped[int] = mapped_column(
            ForeignKey('user.id'),
            nullable=False
        )

        pipeline_id: Mapped[int] = mapped_column(
            ForeignKey('pipeline.id'),
            nullable=False
        )

        destination: Mapped[str] = mapped_column(nullable=False)
        flow_run_id: Mapped[str] = mapped_column(nullable=True)

        date_started: Mapped[datetime] = mapped_column(
            nullable=False,
            default=datetime.now
        )

        validation_results: Mapped[List[Dict[str, Any]]] = mapped_column(
            JSONB,
            nullable=False,
            default=[]
        )

        completed: Mapped[bool] = mapped_column(
            nullable=False,
            default=False
        )

        failure_message: Mapped[str | None] = mapped_column(
            nullable=True,
        )

        pipeline: Mapped['Pipeline'] = relationship(
            back_populates='uploads',
            foreign_keys=[pipeline_id]
        )

        user: Mapped['User'] = relationship( # noqa F821
            back_populates='user_uploads',
            foreign_keys=[user_id]
        )

    class _UserMixin:

        @declared_attr
        def user_uploads(self) -> Mapped[list[Upload]]:
            return relationship(
                'Upload',
                back_populates='user'
            )

    return PipelineStepModels(
        pipeline=Pipeline,
        pipeline_step=PipelineStep,
        upload=Upload,
        _user_mixin=_UserMixin
    )
