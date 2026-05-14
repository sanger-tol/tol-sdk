# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from tol.board.errors import CopyError, NotFoundError, PayloadError

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
    collect_recursive_fn: Callable[..., dict[str, list[DataObject]]],
    save_board_entity_and_children_fn: Callable[..., tuple[str | None, dict[str, str]]],
    serialise_board_entities_fn: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], int]:
    obj = board_ds.get_one(object_type, object_id)
    if obj is None or obj.id is None:
        raise NotFoundError(object_type)

    required_payload_fields = ['parent_entity_id']
    if not all(field in payload for field in required_payload_fields):
        raise PayloadError(
            f'You must specify all of: {", ".join(required_payload_fields)}'
        )

    new_parent_title = payload.get('new_parent_entity_title', f'{obj.title} - copy')
    parent_type = str(payload.get('parent_entity_type', 'board'))
    parent_id = payload.get('parent_entity_id', None)

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
        raise CopyError(object_type)

    copied_entity = serialise_board_entities_fn(all_entities, obj.id, type_hierarchy, id_mapping)
    copied_entity['title'] = new_parent_title

    return copied_entity, 201
