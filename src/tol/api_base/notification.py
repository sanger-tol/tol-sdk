# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, request

from pydantic import ValidationError

from .auth import ForbiddenError
from .misc import CtxGetter, default_ctx_getter
from ..core import DataSourceError, ErrorObject
from ..rabbitmq.schema import NotificationRequest, wrap_in_envelope

if TYPE_CHECKING:
    from ..rabbitmq import RabbitmqDataSource


def notification_blueprint(
    rabbitmq_ds: RabbitmqDataSource,
    url_prefix: str = '/notification',
    role: str | None = None,
    ctx_getter: CtxGetter = default_ctx_getter
) -> Blueprint:
    """
    A flask `Blueprint` exposing an endpoint for publishing
    notification requests to RabbitMQ.
    """

    bp = Blueprint(
        'notification',
        __name__,
        url_prefix=url_prefix
    )

    @bp.post('')
    def notify() -> tuple[dict[str, str], int]:
        """Validate and publish a `NotificationRequest`"""
        if role is not None:
            ctx = ctx_getter()
            if role not in ctx.roles:
                raise ForbiddenError()

        body = request.get_json(silent=True) or {}

        try:
            notification_request = NotificationRequest.model_validate(body)
        except ValidationError as e:
            raise DataSourceError(
                'Bad Request',
                str(e.errors()),
                400
            )

        message = rabbitmq_ds.data_object_factory(
            'notification_message',
            id_=notification_request.id,
            attributes={
                'body': wrap_in_envelope(notification_request)
            }
        )

        results = rabbitmq_ds.insert_batch('notification_message', [message])

        # RabbitmqDataSource.insert_batch always returns a list with one
        # entry per input object - None/empty cannot occur here.
        if results is None:
            raise DataSourceError(
                'Insert Failed',
                f'could not insert id: {notification_request.id}, \
                    message: {message} into RabbitMQ queue.',
                500
            )

        results_list = list(results)

        first = results_list[0]
        if isinstance(first, ErrorObject):
            raise DataSourceError(
                'Publish Failed',
                str(first.details),
                500
            )

        return {'notification_id': notification_request.id}, 202

    return bp
