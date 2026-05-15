# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from tol.api_base.misc.auth_context import CtxGetter, default_ctx_getter
from tol.board.errors import NotFoundError

if TYPE_CHECKING:
    from ..core import DataObject
    from ..sql import SqlDataSource


def get_entity(
    *,
    board_ds: SqlDataSource,
    object_type: str,
    object_id: str,
    type_hierarchy: list[str],
    collect_recursive_fn: Callable[..., dict[str, list[DataObject]]],
    serialise_board_entities_fn: Callable[..., dict[str, Any]],
    ctx_getter: CtxGetter = default_ctx_getter,
) -> tuple[dict[str, Any], int]:
    obj = board_ds.get_one(object_type, object_id)
    if obj is None or obj.id is None:
        raise NotFoundError(object_type)

    all_entities = collect_recursive_fn(board_ds, object_type, [obj], type_hierarchy)
    serialised_entities = serialise_board_entities_fn(
        all_entities,
        obj.id,
        type_hierarchy,
        id_mapping=None,
        board_ds=board_ds,
        ctx_getter=ctx_getter,
    )

    return serialised_entities, 200
