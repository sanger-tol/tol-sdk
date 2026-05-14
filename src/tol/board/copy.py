# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import DataObject
    from ..sql import SqlDataSource


def copy_entity(
    *,
    board_ds: SqlDataSource,
    object_type: str,
    object_id: str,
    type_hierarchy: list[str],
    user_id: str,
    payload: dict[str, Any],
    not_found_error_type: type[Exception],
    copy_error_type: type[Exception],
    collect_recursive_fn: Callable[..., dict[str, list[DataObject]]],
    save_board_entity_and_children_fn: Callable[..., tuple[str | None, dict[str, str]]],
    serialise_board_entities_fn: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], int]:
    obj = board_ds.get_one(object_type, object_id)
    if obj is None or obj.id is None:
        raise not_found_error_type(object_type)

    new_parent_title = payload.get('new_parent_entity_title', f'{obj.title} - copy')
    parent_type = str(payload.get('parent_entity_type', 'board'))
    raw_parent_id = payload.get('parent_entity_id')
    parent_id = str(raw_parent_id) if raw_parent_id is not None else None

    all_entities = collect_recursive_fn(board_ds, object_type, [obj], type_hierarchy)
    new_entity_id, id_mapping = save_board_entity_and_children_fn(
        board_ds,
        all_entities,
        user_id,
        new_parent_title,
        parent_type,
        type_hierarchy,
        object_type=object_type,
        parent_id=parent_id,
    )

    if not all_entities.get(object_type) or not new_entity_id:
        raise copy_error_type(object_type)

    copied_entity = serialise_board_entities_fn(all_entities, obj.id, type_hierarchy, id_mapping)
    copied_entity['title'] = new_parent_title

    return copied_entity, 201
