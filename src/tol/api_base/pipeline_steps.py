# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from flask import Blueprint, request

from .auth import ForbiddenError
from .misc import (
    CtxGetter,
    default_ctx_getter
)
from ..core import (
    DataSourceError,
    DataSourceFilter
)

if typing.TYPE_CHECKING:
    from ..prefect import PrefectDataSource
    from ..sql import SqlDataSource


@dataclass
class UploadData:
    s3_bucket: str
    s3_filename: str
    spreadsheet_config: str
    pipeline_id: int
    destination: str
    upload_name: str
    user_id: int
    dry_run: bool


REQUIRED_FIELDS: List = [
    's3_bucket',
    's3_filename',
    'spreadsheet_config',
    'pipeline_id',
    'upload_name',
    'destination',
    'dry_run'
]


def pipeline_steps_blueprint(
    sql_ds: SqlDataSource,
    prefect_ds: PrefectDataSource,
    role: str | None = None,
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
                's3_bucket': upload_data.s3_bucket,
                's3_filename': upload_data.s3_filename,
                'spreadsheet_config': upload_data.spreadsheet_config,
                'upload_name': upload_data.upload_name,
                'pipeline_id': upload_data.pipeline_id,
                'destination': upload_data.destination,
                'user_id': upload_data.user_id,
                'validation_status': 'validation_in_progress'
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

        if pipeline_id is None:
            raise DataSourceError(
                'Bad Request',
                'Pipeline ID must be provided to run the pipeline.',
                400
            )
        
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
                    f'app_name: {os.environ.get("APP_NAME", "tol")}',
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

    def __check_auth(ctx: Any = None) -> None:
        if role is not None:
            if not ctx or not ctx.authenticated:
                raise ForbiddenError()
            if role not in ctx.roles:
                raise ForbiddenError()

    @bp.route('/revalidate', methods=['POST'])
    def revalidate_upload() -> tuple[dict[str, str], int]:

        allowed_validation_statuses = ['validation_system_error', 'validation_timeout']

        ctx = ctx_getter()
        __check_auth(ctx)

        body: dict[str, Any] = request.json.get('data', {})
        __check_required_fields(body, required_fields=['upload_ids'])

        upload_ids: list[str] = body['upload_ids']

        f = DataSourceFilter()
        f.and_ = {
            'id': {'in_list': {'value': upload_ids}}}

        existing_uploads = sql_ds.get_list(
            'upload',
            object_filters=f
        )

        if not existing_uploads:
            raise DataSourceError(
                'Not Found',
                'No uploads found for the provided upload IDs.',
                404
            )

        existing_by_id = {upload.id: upload for upload in existing_uploads}

        for upload in existing_uploads:
            if upload.validation_status not in allowed_validation_statuses:
                raise DataSourceError(
                    'Invalid Request',
                    f'Upload with ID {upload.id} cannot be revalidated as its validation \
                    status is not in {allowed_validation_statuses} status.',
                    400
                )

        uploads = [sql_ds.data_object_factory(
            'upload',
            upload_id,
            attributes={
                'validation_status': 'validation_in_progress',
                'rejection_reason': None,
                'date_started': datetime.now(),
                'failure_message': None,
                'validation_results': [],
                'completed': False,
                'flow_run_id': None
            },
        ) for upload_id in upload_ids]

        if not uploads:
            raise DataSourceError(
                'Not Found',
                'No uploads found for the provided upload IDs.',
                404
            )

        sql_ds.upsert(
            'upload',
            uploads
        )

        flow_run_ids = [__insert_flow_run(
            upload_id=upload_id,
            pipeline_id=existing_by_id[upload_id].pipeline.id,
            s3_filename=existing_by_id[upload_id].s3_filename,
            dry_run=False
        ) for upload_id in upload_ids]

        for upload_id, flow_run_id in zip(upload_ids, flow_run_ids):
            __upsert_flow_run_id(
                upload_id=upload_id,
                flow_run_id=flow_run_id
            )

        return {'success': True, 'upload_and_flow_run_ids': list(zip(upload_ids,
                                                                     flow_run_ids))}, 200

    @bp.post('')
    def run_pipeline_steps() -> tuple[dict[str, Any], int]:

        ctx = ctx_getter()
        __check_auth(ctx)

        user_id = ctx.user_id if ctx and ctx.authenticated else None

        body: dict[str, Any] = request.json.get('data', {})

        __check_required_fields(body)

        pipeline_id: str = body['pipeline_id']

        __get_pipeline(pipeline_id)

        upload_data = UploadData(
            s3_bucket=body['s3_bucket'],
            s3_filename=body['s3_filename'],
            spreadsheet_config=body['spreadsheet_config'],
            pipeline_id=pipeline_id,
            destination=body['destination'],
            upload_name=body['upload_name'],
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
