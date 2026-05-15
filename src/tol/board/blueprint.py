# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, request

from .constants import TYPE_HIERARCHY
from .copy import copy_entity
from .create import add_entity, create_board
from .delete import delete_entity
from .errors import (
    PayloadError,
    UnknownTypeError,
)
from .get import get_entity
from .reorder import reorder_entities
from .utils import (
    collect_recursive,
    get_entity_type_from_prefix,
    get_parent_joiner_objs,
    save_board_entity_and_children,
    serialise_board_entities,
)
from ..api_base.misc import CtxGetter, default_ctx_getter
from ..core import DataSourceError

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def board_blueprint(
    board_ds: SqlDataSource,
    type_hierarchy: list[str] = TYPE_HIERARCHY,
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
    def __copy_entity(*, object_type: str, object_id: str):
        return copy_entity(
            board_ds=board_ds,
            object_type=object_type,
            object_id=object_id,
            type_hierarchy=type_hierarchy,
            user_id=ctx_getter().user_id,
            payload=request.json or {},
            collect_recursive_fn=collect_recursive,
            save_board_entity_and_children_fn=save_board_entity_and_children,
            serialise_board_entities_fn=serialise_board_entities,
        )

    @board_bp.post('/add-entity/<string:object_type>/<string:parent_id>')
    def __add_entity_endpoint(*, object_type: str, parent_id: str):
        ctx = ctx_getter()
        return add_entity(
            board_ds=board_ds,
            type_hierarchy=type_hierarchy,
            object_type=object_type,
            parent_id=parent_id,
            user_id=ctx.user_id,
            roles=ctx.roles,
            payload=request.json or {},
            get_entity_type_from_prefix_fn=get_entity_type_from_prefix,
        )

    @board_bp.post('/create-board')
    def __create_board_endpoint():
        return create_board(
            board_ds=board_ds,
            type_hierarchy=type_hierarchy,
            user_id=ctx_getter().user_id,
            payload=request.json or {},
        )

    @board_bp.delete('/<string:object_type>/<string:object_id>')
    def __delete_endpoint(*, object_type: str, object_id: str):
        if object_type not in type_hierarchy:
            raise UnknownTypeError()

        ctx = ctx_getter()
        delete_entity(
            board_ds=board_ds,
            type_hierarchy=type_hierarchy,
            parent_type=object_type,
            parent_id=object_id,
            user_id=ctx.user_id,
            roles=ctx.roles,
        )

        return {'deleted': True}, 200

    @board_bp.patch('/reorder/<string:parent_object_id>')
    def __reorder_endpoint(*, parent_object_id: str):
        """
        Reorders child entities under a given parent entity.

        Expects a JSON body with an 'order' field containing a
        list of child entity IDs in the desired order.

        Validates that the provided order includes all and only the actual child IDs.
        """
        payload = request.json or {}
        new_order = payload.get('order')

        if 'order' not in payload:
            raise PayloadError(['order'])

        if not isinstance(new_order, list) or not all(isinstance(item, str) for item in new_order):
            raise DataSourceError(
                'Bad Request',
                'The field "order" must be a list of strings.',
                400,
            )

        reorder_entities(
            board_ds=board_ds,
            parent_object_id=parent_object_id,
            new_order=new_order,
            get_entity_type_from_prefix_fn=get_entity_type_from_prefix,
            get_parent_joiner_objs_fn=get_parent_joiner_objs,
        )

        return {
            'order': new_order,
        }, 200

    @board_bp.get('/get-entity/<string:object_type>/<string:object_id>')
    def __get_board_entities(*, object_type: str, object_id: str):
        return get_entity(
            board_ds=board_ds,
            object_type=object_type,
            object_id=object_id,
            type_hierarchy=type_hierarchy,
            collect_recursive_fn=collect_recursive,
            serialise_board_entities_fn=serialise_board_entities,
        )

    return board_bp
