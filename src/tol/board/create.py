# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from ..core import DataSourceFilter

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def add_entity(
    *,
    board_ds: SqlDataSource,
    type_hierarchy: list[str],
    object_type: str,
    parent_id: str,
    user_id: str,
    roles: list[str],
    payload: dict[str, Any],
    add_error_type: type[Exception],
    bad_parent_error_type: type[Exception],
    not_found_error_type: type[Exception],
    unknown_type_error_type: type[Exception],
    forbidden_error_type: type[Exception],
    get_entity_type_from_prefix_fn: Callable[[str], str | None],
    generate_entity_id_fn: Callable[..., str],
    serialise_board_entities_fn: Callable[..., dict[str, Any]],
    id_generator: Callable[..., str],
) -> tuple[dict[str, Any], int]:
    if object_type not in type_hierarchy:
        raise unknown_type_error_type()

    object_index = type_hierarchy.index(object_type)
    if object_index == 0:
        raise add_error_type(object_type)

    expected_parent_type = type_hierarchy[object_index - 1]
    parent_type = get_entity_type_from_prefix_fn(parent_id.split('_', 1)[0])
    if parent_type is None or parent_type != expected_parent_type:
        raise bad_parent_error_type(expected_parent_type)

    parent_obj = board_ds.get_one(parent_type, parent_id)
    if parent_obj is None or parent_obj.id is None:
        raise not_found_error_type(parent_type)

    if getattr(parent_obj.user, 'id', None) != user_id and 'warden' not in roles:
        raise forbidden_error_type()

    attributes = payload.get('attributes', {})

    if 'title' not in attributes:
        attributes['title'] = f'New {object_type}'

    if object_type in ('board', 'view', 'zone', 'component') and 'filter' not in attributes:
        attributes['filter'] = {}

    new_entity_id = generate_entity_id_fn(
        object_type,
        id_generator=id_generator,
        fallback_prefix=object_type[:1],
    )

    user_stub = board_ds.data_object_factory(
        type_='user',
        id_=user_id,
    )

    new_entity = board_ds.data_object_factory(
        type_=object_type,
        id_=new_entity_id,
        attributes=attributes,
        to_one={'user': user_stub},
    )
    board_ds.insert(object_type, [new_entity])

    joiner_type = f'{object_type}_{parent_type}'
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

    join_obj = board_ds.data_object_factory(
        type_=joiner_type,
        attributes={'order': next_order},
        to_one={
            object_type: board_ds.data_object_factory(
                type_=object_type,
                id_=new_entity_id,
            ),
            parent_type: board_ds.data_object_factory(
                type_=parent_type,
                id_=parent_id,
            ),
        },
    )
    board_ds.insert(joiner_type, [join_obj])

    serialised_entity = serialise_board_entities_fn(
        {object_type: [new_entity]},
        new_entity_id,
        type_hierarchy,
    )

    if not serialised_entity:
        serialised_entity = {
            'id': new_entity_id,
            'type': object_type,
            **{
                k: v for k, v in attributes.items()
                if k != 'filter' or object_type in ('component', 'zone')
            },
        }
        if object_type != 'component':
            serialised_entity['order'] = []
            serialised_entity['children'] = {}

    return {
        **serialised_entity,
        'parent_id': parent_id,
        'parent_order': next_order,
    }, 201


def create_board(
    *,
    board_ds: SqlDataSource,
    type_hierarchy: list[str],
    user_id: str,
    payload: dict[str, Any],
    generate_entity_id_fn: Callable[..., str],
    serialise_board_entities_fn: Callable[..., dict[str, Any]],
    id_generator: Callable[..., str],
) -> tuple[dict[str, Any], int]:
    board_title = payload.get('board_title', 'Untitled board')
    first_view_title = payload.get('first_view_title', 'View 1')

    board_type = type_hierarchy[0]
    view_type = type_hierarchy[1]

    board_id = generate_entity_id_fn(board_type, id_generator=id_generator)

    user_stub = board_ds.data_object_factory(
        type_='user',
        id_=user_id,
    )

    board_obj = board_ds.data_object_factory(
        type_=board_type,
        id_=board_id,
        attributes={
            'title': board_title,
            'filter': {},
        },
        to_one={'user': user_stub},
    )
    board_ds.insert(board_type, [board_obj])

    view_attributes = {
        'title': first_view_title,
        'filter': {},
    }

    view_id = generate_entity_id_fn(view_type, id_generator=id_generator)

    view_obj = board_ds.data_object_factory(
        type_=view_type,
        id_=view_id,
        attributes=view_attributes,
        to_one={'user': user_stub},
    )
    board_ds.insert(view_type, [view_obj])

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
    existing_joins = list(board_ds.get_list(joiner_type, object_filters=joins_filter))
    next_order = max((getattr(join, 'order', 0) for join in existing_joins), default=0) + 1

    view_board_obj = board_ds.data_object_factory(
        type_=joiner_type,
        attributes={'order': next_order},
        to_one={
            view_type: board_ds.data_object_factory(
                type_=view_type,
                id_=view_id,
            ),
            board_type: board_ds.data_object_factory(
                type_=board_type,
                id_=board_id,
            ),
        },
    )
    board_ds.insert(joiner_type, [view_board_obj])

    entities = {
        board_type: [board_obj],
        view_type: [view_obj],
        joiner_type: [view_board_obj],
    }
    serialised = serialise_board_entities_fn(entities, board_id, type_hierarchy)

    return serialised, 201
