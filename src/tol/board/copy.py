# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING


from .constants import TYPE_HIERARCHY
from .errors import CopyError, NotFoundError
from .utils import (
    collect_recursive,
    save_board_entity_and_children,
    serialise_board_entities
)

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def copy_entity(
    board_ds: SqlDataSource,
    object_type: str,
    object_id: str,
    user_id: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    obj = board_ds.get_one(object_type, object_id)
    if obj is None or obj.id is None:
        raise NotFoundError(object_type)

    new_parent_title = payload.get('new_parent_entity_title', f'{obj.title} - copy')
    parent_type = str(payload.get('parent_entity_type', 'board'))
    parent_id = payload.get('parent_entity_id', None)

    all_entities = collect_recursive(board_ds, object_type, [obj])
    new_entity_id, id_mapping = save_board_entity_and_children(
        board_ds,
        all_entities,
        user_id,
        new_parent_title,
        parent_type,
        object_type,
        parent_id,
    )

    if not all_entities.get(object_type) or not new_entity_id:
        raise CopyError(object_type)

    copied_entity = serialise_board_entities(
        all_entities, obj.id, TYPE_HIERARCHY, board_ds, id_mapping)
    copied_entity['title'] = new_parent_title

    return copied_entity, 201
