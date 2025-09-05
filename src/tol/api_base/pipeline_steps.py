# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from typing import Any, List

from flask import Blueprint, request

from .auth import ForbiddenError
from .misc import (
    CtxGetter,
    default_ctx_getter
)
from ..core import (
    DataSourceError
)

if typing.TYPE_CHECKING:
    from ..prefect import PrefectDataSource
    from ..sql import SqlDataSource


@dataclass
class UploadData:
    s3_url: str
    s3_filename: str
    spreadsheet_config: str
    pipeline_id: int
    destination: str
    user_id: int
    dry_run: bool


REQUIRED_FIELDS: List = [
    's3_url',
    's3_filename',
    'spreadsheet_config',
    'pipeline_id',
    'destination',
    'dry_run'
]


def pipeline_steps_blueprint(
    sql_ds: SqlDataSource,
    prefect_ds: PrefectDataSource,
    role: str | None = 'exporter',
    url_prefix: str = '/run-pipeline',

    ctx_getter: CtxGetter = default_ctx_getter,
) -> Blueprint:
    """
    A flask `Blueprint` providing endpoints
    for running validations on uploaded manifests.

    E.g. running a Tree of Sex validation pipeline
    on a spreadsheet manifest using `PrefectDataSource`.
    """

    bp = Blueprint(
        'pipeline-steps',
        __name__,
        url_prefix=url_prefix
    )

    def __check_required_fields(
        body: dict[str, Any],
        required_fields: list[str] = REQUIRED_FIELDS
    ) -> None:

        if not all(field in body for field in required_fields):
            raise DataSourceError(
                'Bad Request',
                f'You must specify all of: {", ".join(required_fields)}',
                400
            )

    def __get_pipeline(
        pipeline_id: int
    ) -> str:

        pipeline = sql_ds.get_one(
            'pipeline',
            pipeline_id
        )

        if not pipeline:
            raise DataSourceError(
                'Not Found',
                'The specified pipeline was not found.',
                404
            )

        return pipeline.id

    def __insert_upload_data(
        upload_data: UploadData
    ) -> str:

        upload = sql_ds.data_object_factory(
            'upload',
            attributes={
                's3_url': upload_data.s3_url,
                's3_filename': upload_data.s3_filename,
                'spreadsheet_config': upload_data.spreadsheet_config,
                'pipeline_id': upload_data.pipeline_id,
                'destination': upload_data.destination,
                'user_id': upload_data.user_id
            },
        )

        inserted_upload_data = list(
            sql_ds.insert(
                'upload',
                [upload]
            )
        )

        if not inserted_upload_data:
            raise DataSourceError(
                'Insertion Error',
                'Failed to insert upload data.',
                500
            )

        return inserted_upload_data[0].id

    def __insert_flow_run(
        upload_id: str,
        pipeline_id: str,
        s3_filename: str,
        dry_run: bool = False,
        flow_name: str = 'pipeline',
    ) -> str | None:

        flow_params = {
            'upload_id': upload_id,
            'pipeline_id': pipeline_id,
            'dry_run': dry_run,
            'source_kwargs': {
                's3_filename': s3_filename,
                's3_bucket': os.environ['UPLOAD_S3_BUCKET'],
            }
        }

        flow_run = prefect_ds.data_object_factory(
            'flow_run',
            attributes={
                'flow_name': flow_name,
                'deployment_name': flow_name,
                'parameters': flow_params,
                'tags': [
                    'app_name:treeofsex',
                ],
            }
        )

        inserted_flow_data = list(
            prefect_ds.insert(
                'flow_run',
                [flow_run]
            )
        )[0]
        return inserted_flow_data.id

    def __upsert_flow_run_id(
        upload_id: str,
        flow_run_id: str
    ) -> None:

        upload = sql_ds.data_object_factory(
            'upload',
            upload_id,
            attributes={
                'flow_run_id': flow_run_id
            }
        )

        sql_ds.upsert(
            'upload',
            [upload]
        )

    @bp.post('')
    def run_pipeline_steps() -> tuple[dict[str, Any], int]:

        ctx = ctx_getter()
        user_id = ctx.user_id

        if role is not None and role not in ctx.roles:
            raise ForbiddenError()

        body: dict[str, Any] = request.json.get('data', {})

        __check_required_fields(body)

        pipeline_id: str = body['pipeline_id']

        __get_pipeline(pipeline_id)

        upload_data = UploadData(
            s3_url=body['s3_url'],
            s3_filename=body['s3_filename'],
            spreadsheet_config=body['spreadsheet_config'],
            pipeline_id=pipeline_id,
            destination=body['destination'],
            user_id=user_id,
            dry_run=body['dry_run']
        )

        upload_id = body.get('upload_id') if body.get('upload_id') is not None \
            else __insert_upload_data(upload_data)

        flow_run_id = __insert_flow_run(
            upload_id=upload_id,
            pipeline_id=pipeline_id,
            s3_filename=upload_data.s3_filename,
            dry_run=upload_data.dry_run
        )

        __upsert_flow_run_id(
            upload_id=upload_id,
            flow_run_id=flow_run_id
        )

        return {'success': True, 'upload_id': upload_id, 'flow_run_id': flow_run_id}, 200

    return bp
