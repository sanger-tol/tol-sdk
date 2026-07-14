# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from tol.board.errors import InvalidOrderError
from tol.board.utils import (
    get_entity_and_child_type_from_parent_id,
    get_parent_joiner_objs
)

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def reorder_entities(
    *,
    board_ds: SqlDataSource,
    parent_object_id: str,
    new_order: list[str],
) -> None:
    """
    Reorders the child entities of a parent entity.

    Args:
        board_ds (SqlDataSource): The data source for board entities.
        parent_object_id (str): The ID of the parent entity.
        new_order (list[str]): The new order of child entity IDs.

    Raises:
        InvalidOrderError: If the new order is invalid.
    """

    parent_type, child_type = get_entity_and_child_type_from_parent_id(parent_object_id)

    if child_type is None:
        raise InvalidOrderError()

    joiner_object_type = f'{child_type}_{parent_type}'

    joiner_objs = get_parent_joiner_objs(
        board_ds,
        parent_object_id,
        joiner_object_type,
    )

    actual_child_ids: list[str] = []

    for obj in joiner_objs:
        child_rel = obj.to_one_relationships.get(child_type)
        child_id = getattr(child_rel, 'id', None)
        if child_id is None:
            raise InvalidOrderError()
        actual_child_ids.append(child_id)

    if len(actual_child_ids) != len(new_order) or set(actual_child_ids) != set(new_order):
        raise InvalidOrderError()

    joiner_ids_by_child_id: dict[str, str] = {}
    for obj in joiner_objs:
        child_rel = obj.to_one_relationships.get(child_type)
        child_id = getattr(child_rel, 'id', None)
        joiner_id = getattr(obj, 'id', None)
        if child_id is None or joiner_id is None:
            raise InvalidOrderError()
        joiner_ids_by_child_id[child_id] = joiner_id

    updated_joiners = [
        board_ds.data_object_factory(
            type_=joiner_object_type,
            id_=joiner_ids_by_child_id[child_id],
            attributes={'order': order},
        )
        for order, child_id in enumerate(new_order)
    ]

    board_ds.upsert(joiner_object_type, updated_joiners)
