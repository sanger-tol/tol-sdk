# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from datetime import datetime, timezone
from typing import Any, List

from flask import Blueprint, request

from .auth import ForbiddenError
from .misc import (
    CtxGetter,
    default_ctx_getter
)
from ..core import (
    DataObject,
    DataSourceError,
    DataSourceFilter
)

if typing.TYPE_CHECKING:
    from ..prefect import PrefectDataSource
    from ..sql import SqlDataSource

REQUIRED_FIELDS: List = [
    's3_url',
    's3_filename',
    'spreadsheet_config',  # Are we always specifying this?
    'pipeline_name',
    'destination',
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
                f'You must specify all of: "{", ".join(required_fields)}"',
                400
            )

    def __get_pipeline(
        pipeline_name: str
    ) -> DataObject:

        f = DataSourceFilter(
            and_={
                'name': {
                    'eq': {
                        'value': pipeline_name
                    }
                }
            }
        )

        pipeline_list = list(
            sql_ds.get_list(
                'pipeline',
                object_filters=f
            )
        )

        if not pipeline_list:
            raise DataSourceError(
                "Not Found",
                "The specified pipeline was not found.",
                404
            )

        return pipeline_list[0]

    def __insert_upload_data():
        pass

    def __insert_flow_run():
        pass

    def __upsert_flow_run_id():
        pass

    @bp.post('')
    def run_pipeline_steps() -> dict[str, Any]:

        ctx = ctx_getter()
        # user_id = ctx.user_id

        if role is not None and role not in ctx.roles:
            raise ForbiddenError()

        body: dict[str, Any] = request.json.get('data', {})

        __check_required_fields(body)

        # s3_url = body['s3_url']
        # s3_filename = body['s3_filename']
        # spreadsheet_config = body['spreadsheet_config']
        pipeline_name = body['pipeline_name']
        # destination = body['destination']

        pipeline = __get_pipeline(pipeline_name)

        print(pipeline)

    return bp
