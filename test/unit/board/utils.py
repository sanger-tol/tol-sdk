# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import count
from typing import Any, Callable, Iterator
from unittest.mock import create_autospec

from tol.core import DataObject, DataSourceFilter


def mock_board_obj(
    type_: str,
    id_: str | None = None,
    attributes: dict[str, Any] = {},
    to_one: dict[str, DataObject] = {},
    user_id: str | None = None
) -> DataObject:
    """Creates a mock DataObject for a board entity."""

    obj: DataObject = create_autospec(DataObject)

    obj.type = type_
    obj.id = id_

    obj._to_one_objects = to_one
    for k, v in to_one.items():
        setattr(obj, k, v)

    obj.attributes = attributes
    for k, v in attributes.items():
        setattr(obj, k, v)

    if user_id is not None:
        user = mock_board_obj('user', user_id)
        obj.user = user
        obj._to_one_objects['user'] = user

    return obj


def mock_board_join(
    objs: dict[str, dict[str, DataObject]],
    bigger: str,
    joiner: str,
    smaller: str,
    type_def: dict[str, tuple[str, list[str]]],
    join_ids: Iterator[str]
) -> dict[str, DataObject]:
    """Creates mock joining table objects linking smaller entities to bigger parents."""

    all_pairs = (
        (k, v)
        for k, (_, v_list) in type_def.items()
        for v in v_list
    )

    join_defs = (
        (
            str(next(join_ids)),
            (
                objs[bigger][k],
                objs[smaller][v]
            )
        )
        for k, v in all_pairs
    )

    return {
        id_: mock_board_obj(
            joiner,
            id_=id_,
            to_one={
                bigger: bigger_obj,
                smaller: smaller_obj
            }
        )
        for id_, (bigger_obj, smaller_obj)
        in join_defs
    }


def mock_board_hierarchy(
    obj_hierachy: dict[str, dict[str, tuple[str, list[str]]]],
    *,
    type_hierarchy: list[str]
) -> dict[str, dict[str, DataObject]]:
    """Mocks all objects in the hierarchy with joins.

    For the smallest one, give an empty list each time.
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
    for i, bigger in enumerate(type_hierarchy[:-1]):
        smaller = type_hierarchy[i + 1]
        joiner = f'{smaller}_{bigger}'

        objs[joiner] = mock_board_join(
            objs,
            bigger,
            joiner,
            smaller,
            obj_hierachy[bigger],
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
        smaller_type, bigger_type = joiner_type.split('_')

        smaller_id = object_filters.and_[f'{smaller_type}.id']['eq']['value']

        # note this is a negate term
        all_bigger_ids = object_filters.and_[f'{bigger_type}.id']['in_list']['value']

        joiner_objs = [
            obj for obj in objs[joiner_type].values()
            if getattr(obj, smaller_type).id == smaller_id
            and getattr(obj, bigger_type).id not in all_bigger_ids
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
        _, bigger = object_type.split('_')

        bigger_id = object_filters.and_[f'{bigger}.id']['eq']['value']

        return [
            obj for obj in objs[object_type].values()
            if getattr(obj, bigger).id == bigger_id
        ]

    return __get_list


