# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from tol.board.constants import TYPE_HIERARCHY

from .errors import CopyError, NotFoundError
from .utils import (
    collect_recursive,
    get_entity_and_child_type_from_parent_id,
    save_board_entity_and_children,
    serialise_board_entities
)

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def copy_entity(
    board_ds: SqlDataSource,
    object_id: str,
    user_id: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """
    Copies a board entity and its children.

    Args:
        board_ds (SqlDataSource): The data source for board entities.
        object_id (str): The ID of the entity to copy.
        user_id (str): The ID of the user performing the copy.
        payload (dict[str, Any]): The payload containing copy details.

    Returns:
        tuple[dict[str, Any], int]: The copied entity and HTTP status code.

    Raises:
        NotFoundError: If the entity to copy does not exist.
        CopyError: If the copy operation fails.
    """

    copy_entity_type, _ = get_entity_and_child_type_from_parent_id(object_id)
    parent_index = TYPE_HIERARCHY.index(copy_entity_type) - 1
    parent_type = TYPE_HIERARCHY[parent_index] if parent_index >= 0 else 'board'

    obj = board_ds.get_one(copy_entity_type, object_id)
    if obj is None or obj.id is None:
        raise NotFoundError(copy_entity_type)

    new_parent_title = payload.get('new_parent_entity_title', f'{obj.title} - copy')
    parent_id = payload.get('parent_entity_id', None)

    all_entities = collect_recursive(board_ds, copy_entity_type, [obj])
    new_entity_id, id_mapping = save_board_entity_and_children(
        board_ds,
        all_entities,
        user_id,
        new_parent_title,
        parent_type,
        copy_entity_type,
        parent_id,
    )

    if not all_entities.get(copy_entity_type) or not new_entity_id:
        raise CopyError(copy_entity_type)

    copied_entity = serialise_board_entities(
        all_entities, obj.id, board_ds, id_mapping)
    copied_entity['title'] = new_parent_title

    return copied_entity, 201
