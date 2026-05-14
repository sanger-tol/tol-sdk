# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import DataObject
    from ..sql import SqlDataSource


def reorder_entities(
    *,
    board_ds: SqlDataSource,
    parent_object_id: str,
    new_order: list[str],
    invalid_order_error_type: type[Exception],
    get_entity_type_from_prefix_fn: Callable[[str], str | None],
    get_parent_joiner_objs_fn: Callable[..., list[DataObject]],
) -> None:
    parent_prefix = parent_object_id.split('_', 1)[0]
    parent_object_type = get_entity_type_from_prefix_fn(parent_prefix) or parent_prefix

    if not new_order:
        raise invalid_order_error_type()

    child_prefix = new_order[0].split('_', 1)[0]
    child_object_type = get_entity_type_from_prefix_fn(child_prefix) or child_prefix

    joiner_object_type = f'{child_object_type}_{parent_object_type}'

    joiner_objs = get_parent_joiner_objs_fn(
        board_ds,
        parent_object_id,
        joiner_object_type,
    )
    actual_child_ids: list[str] = []
    for obj in joiner_objs:
        child_rel = obj.to_one_relationships.get(child_object_type)
        child_id = getattr(child_rel, 'id', None)
        if child_id is None:
            raise invalid_order_error_type()
        actual_child_ids.append(child_id)

    if len(actual_child_ids) != len(new_order) or set(actual_child_ids) != set(new_order):
        raise invalid_order_error_type()

    joiner_ids_by_child_id: dict[str, str] = {}
    for obj in joiner_objs:
        child_rel = obj.to_one_relationships.get(child_object_type)
        child_id = getattr(child_rel, 'id', None)
        joiner_id = getattr(obj, 'id', None)
        if child_id is None or joiner_id is None:
            raise invalid_order_error_type()
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
