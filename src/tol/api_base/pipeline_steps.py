# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import random
import time
import threading
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
    DataSourceError,
    DataSourceFilter
)

if typing.TYPE_CHECKING:
    from ..prefect import PrefectDataSource
    from ..sql import SqlDataSource


@dataclass
class UploadData:
    s3_url: str
    s3_filename: str
    spreadsheet_config: str
    pipeline_name: str
    destination: str
    user_id: int


REQUIRED_FIELDS: List = [
    's3_url',
    's3_filename',
    'spreadsheet_config',
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
    ) -> str:

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
        )[0]

        if not pipeline_list:
            raise DataSourceError(
                "Not Found",
                "The specified pipeline was not found.",
                404
            )

        return pipeline_list.id

    def __insert_upload_data(
        upload_data: UploadData
    ) -> str:

        upload = sql_ds.data_object_factory(
            'upload',
            attributes={**upload_data.__dict__},
        )

        inserted_upload_data = list(
            sql_ds.insert(
                'upload',
                [upload]
            )
        )[0]

        return inserted_upload_data.id

    def __insert_flow_run(
        upload_id: str,
        pipeline_id: str,
    ) -> str:

        # flow_run = prefect_ds.data_object_factory(
        #     'flow_run',
        #     attributes={
        #         'upload_id': upload_id,
        #         'pipeline_id': pipeline_id,
        #     }
        # )

        # inserted_flow_data = list(
        #     prefect_ds.insert(
        #         'flow_run',
        #         [flow_run]
        #     )
        # )[0]

        # return inserted_flow_data.id
        return f'mock_flow_run_id_{upload_id}_{pipeline_id}'

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

    def __upsert_mock_results_data(
        upload_id: str,
    ) -> None:

        time.sleep(random.randint(10, 15))

        mock_step_name = [
            'species_not_null',
            'value_not_allowed',
            'a_third_because_why_not',
            'and_a_fourth'
        ]

        for step_name in mock_step_name:
            mock_results = __create_mock_results(step_name)

            upload = sql_ds.data_object_factory(
                'upload',
                upload_id,
                attributes={
                    'validation_results': mock_results
                }
            )

            sql_ds.upsert(
                'upload',
                [upload]
            )

            time.sleep(random.randint(5, 10))

    def __create_mock_results(
        step_name: str,
    ) -> list[dict[str, Any]]:
        """
        {
        'code': r.code,
        'detail': r.detail,
        'field': r.field,
        'object_id': r.object_id,
        'severity': r.severity.value,
        'step_name': name,
        }
        """

        mock_severity = ['warning', 'error']
        # mock_step_name = ['species_not_null', 'value_not_allowed']
        mock_detail = [
            'Species cannot be null.',
            'Value is not allowed.',
            'Invalid value provided.',
            'Field is required.'
        ]

        def __mock_field_builder() -> str:
            random_field_num = random.randint(1, 4)
            random_fields = ['A', 'B', 'C', 'D', 'E', 'F']

            if random_field_num == 1:
                return None
            elif random_field_num == 2:
                return random.choice(random_fields)
            else:
                fields = random.sample(random_fields, random.randint(2, 4))
                fields.sort()
                return fields

        results = []
        for _ in range(5):
            results.append({
                'code': '',
                'detail': random.choice(mock_detail),
                'field': __mock_field_builder(),
                'object_id': f'{random.randint(1, 10)}',
                'severity': random.choice(mock_severity),
                'step_name': step_name
            })

        return results

    @bp.post('')
    def run_pipeline_steps() -> dict[str, Any]:

        ctx = ctx_getter()
        user_id = ctx.user_id

        if role is not None and role not in ctx.roles:
            raise ForbiddenError()

        body: dict[str, Any] = request.json.get('data', {})

        __check_required_fields(body)

        pipeline_name: str = body['pipeline_name']

        pipeline_id = __get_pipeline(pipeline_name)

        upload_data = UploadData(
            s3_url=body['s3_url'],
            s3_filename=body['s3_filename'],
            spreadsheet_config=body['spreadsheet_config'],
            pipeline_name=pipeline_name,
            destination=body['destination'],
            user_id=user_id
        )

        upload_id = __insert_upload_data(upload_data)

        flow_run_id = __insert_flow_run(
            upload_id=upload_id,
            pipeline_id=pipeline_id
        )

        __upsert_flow_run_id(
            upload_id=upload_id,
            flow_run_id=flow_run_id
        )

        threading.Thread(target=__upsert_mock_results_data, args=(upload_id,), daemon=True).start()

        return {'success': True}, 200

    return bp
