# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import count
from typing import Any, Callable, Iterator
from unittest.mock import MagicMock, create_autospec

from tol.core import DataObject, DataSourceFilter


def mock_board_obj(
    type_: str,
    id_: str | None = None,
    attributes: dict[str, Any] | None = None,
    to_one: dict[str, DataObject] | None = None,
    user_id: str | None = None
) -> DataObject:
    """Creates a mock DataObject for a board entity."""

    resolved_attrs: dict[str, Any] = dict(attributes or {})
    resolved_to_one: dict[str, DataObject] = dict(to_one or {})

    obj: DataObject = create_autospec(DataObject)

    obj.type = type_
    obj.id = id_
    obj.oidc_id = None
    obj.data_source_instance = MagicMock()
    obj.data_source_instance.id = None
    obj.data_source_instance.ui_api_details = None
    obj.order = resolved_attrs.get('order', 0)

    obj._to_one_objects = resolved_to_one
    obj.to_one_relationships = resolved_to_one
    for k, v in resolved_to_one.items():
        setattr(obj, k, v)

    obj.attributes = resolved_attrs
    obj.title = resolved_attrs.get('title', '')
    for k, v in resolved_attrs.items():
        setattr(obj, k, v)

    if user_id is not None:
        user = mock_board_obj('user', user_id, attributes={'oidc_id': 'user@example.com'})
        obj.user = user
        obj._to_one_objects['user'] = user
        obj.to_one_relationships['user'] = user

    return obj


def mock_board_join(
    objs: dict[str, dict[str, DataObject]],
    parent: str,
    joiner: str,
    child: str,
    type_def: dict[str, tuple[str, list[str]]],
    join_ids: Iterator[str]
) -> dict[str, DataObject]:
    """Creates mock joining table objects linking child entities to parent entities."""

    all_pairs = (
        (k, v)
        for k, (_, v_list) in type_def.items()
        for v in v_list
    )

    join_defs = (
        (
            str(next(join_ids)),
            (
                objs[parent][k],
                objs[child][v]
            )
        )
        for k, v in all_pairs
    )

    return {
        id_: mock_board_obj(
            joiner,
            id_=id_,
            to_one={
                parent: parent_obj,
                child: child_obj
            }
        )
        for id_, (parent_obj, child_obj)
        in join_defs
    }


def mock_board_hierarchy(
    obj_hierachy: dict[str, dict[str, tuple[str, list[str]]]],
    *,
    type_hierarchy: list[str]
) -> dict[str, dict[str, DataObject]]:
    """Mocks all objects in the hierarchy with joins.

    For the leaf child, give an empty list each time.
    """

    objs: dict[str, dict[str, DataObject]] = {}

    # build up the exposed types
    for t in type_hierarchy:
        objs[t] = {
            k: mock_board_obj(t, id_=k, user_id=user_id)
            for k, (user_id, _)
            in obj_hierachy.get(t, {}).items()
        }

    join_ids = iter(count())

    # build up the joining types
    for i, parent in enumerate(type_hierarchy[:-1]):
        child = type_hierarchy[i + 1]
        joiner = f'{child}_{parent}'

        objs[joiner] = mock_board_join(
            objs,
            parent,
            joiner,
            child,
            obj_hierachy[parent],
            join_ids
        )

    return objs


def mock_board_get_one(
    objs: dict[str, dict[str, DataObject]]
) -> Callable[[str, str], DataObject | None]:
    """Returns a side_effect function for board_ds.get_one."""

    def __get_one(
        object_type: str,
        object_id: str
    ) -> DataObject | None:
        return objs[object_type].get(object_id)

    return __get_one


def mock_board_get_count(
    objs: dict[str, dict[str, DataObject]]
) -> Callable:
    """Returns a side_effect function for board_ds.get_count."""

    def __get_count(
        joiner_type: str,
        *,
        object_filters: DataSourceFilter
    ) -> int:
        child_type, parent_type = joiner_type.split('_')

        child_id = object_filters.and_[f'{child_type}.id']['eq']['value']

        # note this is a negate term
        all_parent_ids = object_filters.and_[f'{parent_type}.id']['in_list']['value']

        joiner_objs = [
            obj for obj in objs[joiner_type].values()
            if getattr(obj, child_type).id == child_id
            and getattr(obj, parent_type).id not in all_parent_ids
        ]
        return len(joiner_objs)

    return __get_count


def mock_board_get_list(
    objs: dict[str, dict[str, DataObject]]
) -> Callable:
    """Returns a side_effect function for board_ds.get_list."""

    def __get_list(
        object_type: str,
        *,
        object_filters: DataSourceFilter
    ) -> list[DataObject]:
        _, parent = object_type.split('_')

        parent_id = object_filters.and_[f'{parent}.id']['eq']['value']

        return [
            obj for obj in objs[object_type].values()
            if getattr(obj, parent).id == parent_id
        ]

    return __get_list
