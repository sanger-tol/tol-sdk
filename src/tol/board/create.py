# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from tol.api_base.auth.error import ForbiddenError
from tol.api_base.misc.auth_context import CtxGetter
from tol.board.constants import TYPE_HIERARCHY
from tol.board.errors import (
    AddError,
    NotFoundError,
    UnknownTypeError
)

from .utils import (
    generate_entity_id,
    get_entity_and_child_type_from_parent_id,
    serialise_board_entities
)
from ..core import DataSourceFilter

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def add_entity(
    board_ds: SqlDataSource,
    parent_id: str,
    user_id: str,
    roles: list[str],
    payload: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """
    Adds a new entity to the board under the specified parent.

    Args:
        board_ds (SqlDataSource): The data source for board entities.
        parent_id (str): The ID of the parent entity.
        user_id (str): The ID of the user performing the addition.
        roles (list[str]): The roles of the user.
        payload (dict[str, Any]): The payload containing entity details.

    Returns:
        tuple[dict[str, Any], int]: The added entity and HTTP status code.

    Raises:
        NotFoundError: If the parent entity does not exist.
        AddError: If the addition operation fails.
        UnknownTypeError: If the entity type is unknown.
        ForbiddenError: If the user is not allowed to add the entity.
    """

    parent_type, child_type = get_entity_and_child_type_from_parent_id(parent_id)

    if child_type not in TYPE_HIERARCHY:
        raise UnknownTypeError()

    if child_type == TYPE_HIERARCHY[0]:
        raise AddError(child_type)

    parent_obj = board_ds.get_one(parent_type, parent_id)
    if parent_obj is None or parent_obj.id is None:
        raise NotFoundError(parent_type)

    if getattr(parent_obj.user, 'id', None) != user_id and 'warden' not in roles:
        raise ForbiddenError()

    attributes = payload.get('attributes', {})
    attributes['filter'] = attributes.get('filter', {})
    
    if child_type in ('zone') or child_type in ('component'):
        attributes['filter_pass_through'] = False
        attributes['filter_exclude_incoming'] = False

    if child_type in ('zone'):
        attributes['attribute_translations'] = {}
        attributes['auto_translations'] = True

    if child_type in ('component'):
        attributes['config'] = {}

    new_child_id = generate_entity_id(child_type)

    user_stub = board_ds.data_object_factory(
        type_='user',
        id_=user_id,
    )

    joiner_type = f'{child_type}_{parent_type}'
    joins_filter = DataSourceFilter(
        and_={
            f'{parent_type}.id': {
                'eq': {
                    'value': parent_id,
                }
            }
        }
    )
    existing_joins = list(board_ds.get_list(joiner_type, object_filters=joins_filter))
    next_order = max((getattr(join, 'order', 0) for join in existing_joins), default=0) + 1

    next_title_increment = board_ds.get_count(joiner_type, object_filters=joins_filter) + 1

    attributes['title'] = ''

    if child_type == 'view':
        attributes['title'] = f'{child_type.capitalize()} {next_title_increment}'

    with board_ds.get_session() as session:
        new_entity = session.data_object_factory(
            type_=child_type,
            id_=new_child_id,
            attributes=attributes,
            to_one={'user': user_stub},
        )
        session.insert(child_type, [new_entity])

        join_obj = session.data_object_factory(
            type_=joiner_type,
            attributes={'order': next_order},
            to_one={
                child_type: session.data_object_factory(
                    type_=child_type,
                    id_=new_child_id,
                ),
                parent_type: session.data_object_factory(
                    type_=parent_type,
                    id_=parent_id,
                ),
            },
        )
        session.insert(joiner_type, [join_obj])

    serialised_entity = serialise_board_entities(
        {child_type: [new_entity]},
        new_child_id,
        board_ds,
    )

    if not serialised_entity:
        serialised_entity = {
            'id': new_child_id,
            'type': child_type,
            **{
                k: v for k, v in attributes.items()
                if k != 'filter' or child_type in ('component', 'zone')
            },
        }
        if child_type != 'component':
            serialised_entity['order'] = []
            serialised_entity['children'] = {}

    return {
        **serialised_entity,
        'parent_id': parent_id,
    }, 201


def create_board(
    *,
    board_ds: SqlDataSource,
    user_id: str,
    ctx_getter: CtxGetter
) -> tuple[dict[str, Any], int]:
    """
    Creates a new board with an initial view.

    Args:
        board_ds (SqlDataSource): The data source for board entities.
        user_id (str): The ID of the user creating the board.

    Returns:
        tuple[dict[str, Any], int]: The created board and HTTP status code.
    """

    board_type = TYPE_HIERARCHY[0]
    view_type = TYPE_HIERARCHY[1]

    board_id = generate_entity_id(board_type)

    with board_ds.get_session() as session:

        user_stub = session.data_object_factory(
            type_='user',
            id_=user_id,
        )

        user_obj = session.get_one('user', user_id) or user_stub

        board_obj = session.data_object_factory(
            type_=board_type,
            id_=board_id,
            attributes={
                'title': 'Untitled board',
                'filter': {},
            },
            to_one={'user': user_obj},
        )
        session.insert(board_type, [board_obj])

        view_attributes = {
            'title': 'View 1',
            'filter': {},
        }

        view_id = generate_entity_id(view_type)

        view_obj = session.data_object_factory(
            type_=view_type,
            id_=view_id,
            attributes=view_attributes,
            to_one={'user': user_stub},
        )
        session.insert(view_type, [view_obj])

        joiner_type = f'{view_type}_{board_type}'
        joins_filter = DataSourceFilter(
            and_={
                f'{board_type}.id': {
                    'eq': {
                        'value': board_id,
                    }
                }
            }
        )
        existing_joins = list(session.get_list(joiner_type, object_filters=joins_filter))
        next_order = max((getattr(join, 'order', 0) for join in existing_joins), default=0) + 1

        view_board_obj = session.data_object_factory(
            type_=joiner_type,
            attributes={'order': next_order},
            to_one={
                view_type: session.data_object_factory(
                    type_=view_type,
                    id_=view_id,
                ),
                board_type: session.data_object_factory(
                    type_=board_type,
                    id_=board_id,
                ),
            },
        )
        session.insert(joiner_type, [view_board_obj])

    entities = {
        board_type: [board_obj],
        view_type: [view_obj],
        joiner_type: [view_board_obj],
    }
    serialised = serialise_board_entities(
        entities,
        board_id,
        board_ds,
        ctx_getter=ctx_getter
    )

    return serialised, 201
