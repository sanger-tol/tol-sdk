# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, request

from .copy import copy_entity
from .create import add_entity, create_board
from .delete import delete_entity
from .get import get_entity
from .reorder import reorder_entities
from .utils import check_auth_and_required_fields
from ..api_base.misc import CtxGetter, default_ctx_getter
from ..core import DataSourceError

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def board_blueprint(
    board_ds: SqlDataSource,
    ctx_getter: CtxGetter = default_ctx_getter,
) -> Blueprint:
    """
    Provides a flask `Blueprint` for management of
    user-configurable dashboarding resources.
    """

    board_bp = Blueprint(
        'dashboards',
        __name__,
    )

    @board_bp.post('/copy/<string:object_type>/<string:object_id>')
    def __copy_entity_endpoint(*, object_type: str, object_id: str):

        payload = request.json or {}
        ctx = ctx_getter()

        check_auth_and_required_fields(
            ctx_getter,
            payload,
            required_fields=['new_parent_entity_title']
        )

        return copy_entity(
            board_ds,
            object_type,
            object_id,
            ctx.user_id,
            payload,
        )

    @board_bp.post('/add-entity/<string:parent_id>')
    def __add_entity_endpoint(*, parent_id: str):

        payload = request.json or {}
        ctx = ctx_getter()

        check_auth_and_required_fields(
            ctx_getter,
            payload
        )

        return add_entity(
            board_ds,
            parent_id,
            ctx.user_id,
            ctx.roles,
            payload,
        )

    @board_bp.post('/create-board')
    def __create_board_endpoint():

        payload = request.json or {}
        ctx = ctx_getter()

        check_auth_and_required_fields(
            ctx_getter,
            payload
        )

        return create_board(
            board_ds=board_ds,
            user_id=ctx.user_id,
        )

    @board_bp.delete('/<string:object_id>')
    def __delete_endpoint(*, object_id: str):

        payload = request.json or {}
        ctx = ctx_getter()

        check_auth_and_required_fields(
            ctx_getter,
            payload
        )

        delete_entity(
            board_ds=board_ds,
            parent_id=object_id,
            user_id=ctx.user_id,
            roles=ctx.roles,
        )

        return {'deleted': True}, 200

    @board_bp.patch('/reorder/<string:parent_id>')
    def __reorder_endpoint(*, parent_id: str):
        """
        Reorders child entities under a given parent entity.

        Expects a JSON body with an 'order' field containing a
        list of child entity IDs in the desired order.

        Validates that the provided order includes all and only the actual child IDs.
        """
        payload = request.json or {}
        new_order = payload.get('order')

        check_auth_and_required_fields(
            ctx_getter,
            payload,
            required_fields=['order']
        )

        if not isinstance(new_order, list) or not all(isinstance(item, str) for item in new_order):
            raise DataSourceError(
                'Bad Request',
                'The field "order" must be a list of strings.',
                400,
            )

        reorder_entities(
            board_ds=board_ds,
            parent_object_id=parent_id,
            new_order=new_order,
        )

        return {
            'order': new_order,
        }, 200

    @board_bp.get('/get-entity/<string:object_id>')
    def __get_board_entities(*, object_id: str):
        return get_entity(
            board_ds,
            object_id,
            ctx_getter,
        )

    return board_bp
