# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core import DataObject, DataSourceFilter

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def _child_is_deletable(
    *,
    board_ds: SqlDataSource,
    child_obj: DataObject,
    parent_type: str,
    all_parent_ids: list[str],
    joiner_type: str,
) -> bool:
    f = DataSourceFilter(
        and_={
            f'{parent_type}.id': {
                'in_list': {
                    'value': all_parent_ids,
                    'negate': True,
                }
            },
            f'{child_obj.type}.id': {
                'eq': {
                    'value': child_obj.id,
                }
            },
        }
    )
    count = board_ds.get_count(joiner_type, object_filters=f)

    return count == 0


def _get_deletable_children(
    *,
    board_ds: SqlDataSource,
    child_type: str,
    joiner_type: str,
    parent_type: str,
    all_parent_ids: list[str],
    joins: list[DataObject],
    user_id: str,
    roles: list[str],
) -> list[DataObject]:
    all_child_objs: list[DataObject] = [
        getattr(join, child_type)
        for join in joins
    ]

    can_delete_any_owner = 'warden' in roles

    return [
        obj for obj in all_child_objs
        if (can_delete_any_owner or getattr(obj.user, 'id', None) == user_id)
        and _child_is_deletable(
            board_ds=board_ds,
            child_obj=obj,
            parent_type=parent_type,
            all_parent_ids=all_parent_ids,
            joiner_type=joiner_type,
        )
    ]


def _delete_recursive(
    *,
    board_ds: SqlDataSource,
    type_hierarchy: list[str],
    leaf_child_type: str,
    parent_type: str,
    parent_objs: list[DataObject],
    user_id: str,
    roles: list[str],
) -> None:
    all_parent_ids = [obj.id for obj in parent_objs if obj.id is not None]

    if parent_type != leaf_child_type:
        all_deletable_children: list[DataObject] = []
        all_join_ids: list[str] = []

        parent_index = type_hierarchy.index(parent_type)
        child_type = type_hierarchy[parent_index + 1]
        joiner_type = f'{child_type}_{parent_type}'

        for parent_obj in parent_objs:
            joins_filter = DataSourceFilter(
                and_={
                    f'{parent_obj.type}.id': {
                        'eq': {
                            'value': parent_obj.id,
                        }
                    }
                }
            )
            joins = list(board_ds.get_list(joiner_type, object_filters=joins_filter))

            deletable_children = _get_deletable_children(
                board_ds=board_ds,
                child_type=child_type,
                joiner_type=joiner_type,
                parent_type=parent_type,
                all_parent_ids=all_parent_ids,
                joins=joins,
                user_id=user_id,
                roles=roles,
            )
            all_deletable_children.extend(deletable_children)

            join_ids = [
                str(j.id)
                for j in joins
                if getattr(j, 'id', None) is not None
            ]
            all_join_ids.extend(join_ids)

        board_ds.delete(joiner_type, all_join_ids)

        _delete_recursive(
            board_ds=board_ds,
            type_hierarchy=type_hierarchy,
            leaf_child_type=leaf_child_type,
            parent_type=child_type,
            parent_objs=all_deletable_children,
            user_id=user_id,
            roles=roles,
        )

    if all_parent_ids:
        board_ds.delete(parent_type, all_parent_ids)


def _delete_above(
    *,
    board_ds: SqlDataSource,
    type_hierarchy: list[str],
    root_parent_type: str,
    object_type: str,
    object_id: str,
    user_id: str,
    roles: list[str],
    deletion_error_type: type[Exception],
) -> None:
    if object_type == root_parent_type:
        return

    object_index = type_hierarchy.index(object_type)
    above_type = type_hierarchy[object_index - 1]
    joiner_type = f'{object_type}_{above_type}'

    filt = DataSourceFilter(
        and_={
            f'{object_type}.id': {
                'eq': {
                    'value': object_id,
                }
            }
        }
    )

    above_count = board_ds.get_count(joiner_type, object_filters=filt)
    if above_count == 0:
        return
    if above_count > 1:
        raise deletion_error_type(above_type, object_type)

    (joiner_obj,) = list(board_ds.get_list(joiner_type, object_filters=filt))

    if joiner_obj.id is None:
        return

    if 'warden' not in roles:
        above_obj = getattr(joiner_obj, above_type, None)
        if above_obj is None:
            raise deletion_error_type(above_type, object_type)

        above_owner_id = getattr(getattr(above_obj, 'user', None), 'id', None)
        if above_owner_id != user_id:
            raise deletion_error_type(above_type, object_type)

    board_ds.delete(joiner_type, [joiner_obj.id])


def delete_entity(
    *,
    board_ds: SqlDataSource,
    type_hierarchy: list[str],
    parent_type: str,
    parent_id: str,
    user_id: str,
    roles: list[str],
    forbidden_error_type: type[Exception],
    not_found_error_type: type[Exception],
    deletion_error_type: type[Exception],
) -> None:
    leaf_child_type = type_hierarchy[-1]
    root_parent_type = type_hierarchy[0]

    parent_obj = board_ds.get_one(parent_type, parent_id)
    if parent_obj is None:
        raise not_found_error_type(parent_type)

    if getattr(parent_obj.user, 'id', None) != user_id and 'warden' not in roles:
        raise forbidden_error_type()

    _delete_above(
        board_ds=board_ds,
        type_hierarchy=type_hierarchy,
        root_parent_type=root_parent_type,
        object_type=parent_type,
        object_id=parent_id,
        user_id=user_id,
        roles=roles,
        deletion_error_type=deletion_error_type,
    )

    _delete_recursive(
        board_ds=board_ds,
        type_hierarchy=type_hierarchy,
        leaf_child_type=leaf_child_type,
        parent_type=parent_type,
        parent_objs=[parent_obj],
        user_id=user_id,
        roles=roles,
    )
