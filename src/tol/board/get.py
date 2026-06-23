# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from tol.api_base.misc.auth_context import CtxGetter, default_ctx_getter
from tol.board.errors import NotFoundError
from tol.board.utils import (
    collect_recursive,
    get_entity_and_child_type_from_parent_id,
    serialise_board_entities
)

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def get_entity(
    board_ds: SqlDataSource,
    object_id: str,
    ctx_getter: CtxGetter = default_ctx_getter,
) -> tuple[dict[str, Any], int]:
    """
    Retrieves an entity and its children recursively.

    Args:
        board_ds (SqlDataSource): The data source for board entities.
        object_id (str): The ID of the entity to retrieve.
        ctx_getter (CtxGetter, optional):
            The context getter for authentication. Defaults to default_ctx_getter.

    Returns:
        tuple[dict[str, Any], int]: The serialized entity and its HTTP status code.
    """

    parent_type, _ = get_entity_and_child_type_from_parent_id(object_id)

    obj = board_ds.get_one(parent_type, object_id)
    if obj is None or obj.id is None:
        raise NotFoundError('board entity')

    all_entities = collect_recursive(board_ds, parent_type, [obj])
    serialised_entities = serialise_board_entities(
        all_entities,
        obj.id,
        board_ds,
        None,
        ctx_getter,
    )

    return serialised_entities, 200
