# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, request
from tol.board.constants import TYPE_HIERARCHY

from .copy import copy_entity
from .create import add_entity, create_board
from .delete import delete_entity
from .get import get_entity
from .reorder import reorder_entities
from .utils import check_auth_and_required_fields, get_entity_and_child_type_from_parent_id
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

    @board_bp.post('/copy/<string:object_id>')
    def __copy_entity_endpoint(*, object_id: str):
        """
        POST copy a board entity and its children.

        Expects a JSON body with the following fields:
        - new_parent_entity_title (str, required): The title for the copied entity.
        - parent_entity_id (str, optional): The ID of the new parent entity to copy under
        (if not provided, the copied entity will be added at the same level as the original).
        """

        payload = request.json or {}
        ctx = ctx_getter()

        entity_type, _ = get_entity_and_child_type_from_parent_id(object_id)
        entity = board_ds.get_one(entity_type, object_id)

        if entity is None:
            raise DataSourceError(
                'Not Found',
                f'No entity found with ID {object_id}',
                404,
            )

        destination_id = payload.get('parent_entity_id')
        if destination_id:
            destination_type, _ = get_entity_and_child_type_from_parent_id(destination_id)
            destination = board_ds.get_one(destination_type, destination_id)
            destination_owner_id = getattr(destination.user, 'id', None) if destination else None
        elif entity_type == TYPE_HIERARCHY[0]:
            destination_owner_id = None
        else:
            destination_owner_id = getattr(entity.user, 'id', None)

        check_auth_and_required_fields(
            ctx_getter,
            payload,
            owner_id=destination_owner_id,
        )

        return copy_entity(
            board_ds,
            object_id,
            ctx.user_id,
            payload,
        )

    @board_bp.post('/add-entity/<string:parent_id>')
    def __add_entity_endpoint(*, parent_id: str):
        """
        POST add a new entity under a given parent entity.

        Expects a JSON body with the following fields:
        - type (str, required): The type of the entity to add.
        - attributes (dict, optional): A dictionary of attributes for the new entity.
        """

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
        """
        POST create a new board with a given title.

        Expects a JSON body with the following fields:
        - title (str, required): The title for the new board.
        """

        payload = request.json or {}
        ctx = ctx_getter()

        check_auth_and_required_fields(
            ctx_getter,
            payload
        )

        return create_board(
            board_ds=board_ds,
            user_id=ctx.user_id,
            ctx_getter=ctx_getter,
        )

    @board_bp.delete('/delete-entity/<string:object_id>')
    def __delete_endpoint(*, object_id: str):
        """
        DELETE an entity and all its children.

        Expects a JSON body with the following fields:
        - None
        """

        payload = request.get_json(silent=True) or {}
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
        """
        GET an entity and all its children recursively.

        Expects a JSON body with the following fields:
        - None
        """

        return get_entity(
            board_ds,
            object_id,
            ctx_getter,
        )

    return board_bp
