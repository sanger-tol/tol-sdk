# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from datetime import datetime
from typing import Any

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


def action_blueprint(
    sql_ds: SqlDataSource,
    prefect_ds: PrefectDataSource,
    role: str | None = 'exporter',
    url_prefix: str = '/run-action',

    ctx_getter: CtxGetter = default_ctx_getter,
) -> Blueprint:
    """
    A flask `Blueprint` providing endpoints
    for applying actions on rows of a table.

    E.g. sending samples to a flow run using
    `PrefectDataSource`.
    """

    bp = Blueprint(
        'actions',
        __name__,
        url_prefix=url_prefix
    )

    def __check_required_fields(
        body: dict[str, Any],
        required_fields: list[str] = ['ids', 'action_name', 'object_type']
    ) -> None:

        if not all(field in body for field in required_fields):
            raise DataSourceError(
                'Bad Request',
                f'You must specify all of: "{", ".join(required_fields)}"',
                400
            )

    def __get_action(
        object_type: str,
        action_name: str
    ) -> DataObject:

        f = DataSourceFilter(
            and_={
                'name': {
                    'eq': {
                        'value': action_name
                    }
                },
                'object_type': {
                    'eq': {
                        'value': object_type
                    }
                }
            }
        )

        action_list = list(
            sql_ds.get_list(
                'action',
                object_filters=f
            )
        )

        if not action_list:
            raise DataSourceError(
                'Not Found',
                'The specified action was not found',
                404
            )

        return action_list[0]

    def __insert_flow_run(
        action: DataObject,
        flow_params: dict[str, Any],
        user_id: str
    ) -> tuple[str, str]:

        flow_name = action.flow_name
        flow_run = prefect_ds.data_object_factory(
            'flow_run',
            attributes={
                'flow_name': flow_name,
                'deployment_name': flow_name,
                'parameters': flow_params,
                'tags': [
                    'app_name:portal',
                    f'user_id:{user_id}'
                ],
            }
        )

        inserted_run_data = list(
            prefect_ds.insert(
                'flow_run',
                [flow_run]
            )
        )[0]

        return inserted_run_data.id, inserted_run_data.name

    @bp.post('')
    def action():

        ctx = ctx_getter()
        user_id = ctx.user_id

        if role is not None and role not in ctx.roles:
            raise ForbiddenError()

        body: dict[str, Any] = request.json.get('data', {})

        __check_required_fields(body)

        ids: list[str] = body['ids']
        action_name: str = body['action_name']
        object_type: str = body['object_type']
        params: dict[str, Any] = body.get('params', {})

        action = __get_action(object_type, action_name)

        action_params = (
            action.params
            if action.params
            else {}
        )

        flow_params = {
            'extra_params': {
                **params,
                **action_params,
            },
            'user_id': user_id,
            'object_type': object_type,
            'ids': ids
        }

        flow_run_id, flow_run_name = __insert_flow_run(
            action,
            flow_params,
            user_id
        )

        user = sql_ds.get_one('user', user_id)

        user_action_params = {
            **params,
            **action_params,
            'ids': ids,
            'flow_run_id': flow_run_id,
            'flow_run_name': flow_run_name
        }

        user_action = sql_ds.data_object_factory(
            'user_action',
            attributes={
                'ids': ids,
                'params': user_action_params,
                'created_at': datetime.now()
            },
            to_one={
                'user': user,
                'action': action
            }
        )
        sql_ds.insert('user_action', [user_action])

        return {'success': True}, 200

    return bp
