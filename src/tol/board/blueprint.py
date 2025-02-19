# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from flask import Blueprint

from ..api_base.auth import ForbiddenError
from ..api_base.misc import (
    CtxGetter,
    default_ctx_getter
)
from ..core import (
    DataObject,
    DataSourceError,
    DataSourceFilter
)

if typing.TYPE_CHECKING:
    from ..sql import SqlDataSource


TYPE_HIERARCHY = [
    'board',
    'view',
    'zone',
    'component',
]


def board_blueprint(
    board_ds: SqlDataSource,
    type_hierarchy: list[str] = TYPE_HIERARCHY,

    ctx_getter: CtxGetter = default_ctx_getter,
) -> Blueprint:
    """
    Provides a flask `Blueprint` for management of
    user-configurable dashboarding resources.
    """

    board_bp = Blueprint(
        'dashboards',
        __name__
    )

    smallest_type = type_hierarchy[-1]
    biggest_type = type_hierarchy[0]

    def __smaller_is_deletable(
        smaller_obj: DataObject,
        bigger_type: str,
        all_bigger_ids: list[str],
        joiner_type: str
    ) -> bool:
        """
        Reasons a smaller row can't be deleted:

        1. It doesn't belong to the user that
           is initiating the delete (managed by
           the calling function before this one).

        2. Other bigger rows point to this smaller
           (e.g. this `zone` is in another `view`).
        """

        f = DataSourceFilter(
            and_={
                f'{bigger_type}.id': {
                    'in_list': {
                        'value': all_bigger_ids,
                        'negate': True
                    }
                },
                f'{smaller_obj.type}.id': {
                    'eq': {
                        'value': smaller_obj.id
                    }
                },
            }
        )
        count = board_ds.get_count(
            joiner_type,
            object_filters=f
        )

        return count == 0

    def __get_deletable_smallers(
        smaller_type: str,
        joiner_type: str,
        bigger_type: str,
        all_bigger_ids: list[str],
        joins: list[DataObject],
        user_id: str
    ) -> list[DataObject]:
        """
        Given a bigger->smaller relation (e.g.
        `zone` rows in a `view`) and the join
        rows that define it (e.g. `zone_view`),
        this function gets the smaller rows
        (here `zone`) that can be deleted.
        """

        all_smaller_objs: list[DataObject] = [
            getattr(join, smaller_type)
            for join in joins
        ]

        return [
            obj for obj in all_smaller_objs
            if obj.user.id == user_id
            and __smaller_is_deletable(
                obj,
                bigger_type,
                all_bigger_ids,
                joiner_type
            )
        ]

    def __delete_recursive(
        bigger_type: str,
        bigger_objs: list[DataObject],
        user_id: str
    ) -> None:
        """
        Given a list of bigger, containing objects (e.g. `view`),
        deletes the contained objects (`zone`->`component`)
        recursively.

        Stops recursion within a branch in which its head can't
        be deleted.
        """

        all_bigger_ids = [obj.id for obj in bigger_objs]

        if bigger_type != smallest_type:
            all_deletable_smallers = []
            all_join_ids = []

            bigger_index = type_hierarchy.index(bigger_type)
            smaller_type = type_hierarchy[bigger_index + 1]
            joiner_type = f'{smaller_type}_{bigger_type}'

            for bigger_obj in bigger_objs:
                joins_filter = DataSourceFilter(
                    and_={
                        f'{bigger_obj.type}.id': {
                            'eq': {
                                'value': bigger_obj.id
                            }
                        }
                    }
                )
                joins = list(
                    board_ds.get_list(
                        joiner_type,
                        object_filters=joins_filter
                    )
                )

                deletable_smallers = __get_deletable_smallers(
                    smaller_type,
                    joiner_type,
                    bigger_type,
                    all_bigger_ids,
                    joins,
                    user_id
                )
                all_deletable_smallers.extend(deletable_smallers)

                join_ids = [j.id for j in joins]
                all_join_ids.extend(join_ids)

            # delete the joins first
            board_ds.delete(joiner_type, all_join_ids)

            __delete_recursive(smaller_type, all_deletable_smallers, user_id)

        board_ds.delete(bigger_type, all_bigger_ids)

    def __delete_above(
        object_type: str,
        object_id: str,
        user_id: str
    ) -> None:
        """
        Deletes the (sole) joining table entry pointing to the specified
        `object_type`, if it's not the biggest type (aka `board`).

        Fails if:
        - there is more than one joining entry (e.g. `zone_view` -> `zone`)
        - the (sole) joining entry does not belong to the authenticated user
        """

        if object_type == biggest_type:
            return

        object_index = type_hierarchy.index(object_type)
        above_type = type_hierarchy[object_index - 1]
        joiner_type = f'{object_type}_{above_type}'

        f = DataSourceFilter(
            and_={
                f'{object_type}.id': {
                    'eq': {
                        'value': object_id
                    }
                }
            }
        )

        above_count = board_ds.get_count(joiner_type, object_filters=f)
        if above_count == 0:
            return
        if above_count > 1:
            raise DataSourceError(
                'Deletion Error',
                f'More than one {above_type}s instances point '
                f'to this {object_type}.',
                400
            )

        (joiner_obj,) = list(
            board_ds.get_list(
                joiner_type,
                object_filters=f
            )
        )

        above_obj: DataObject = getattr(joiner_obj, above_type)
        if above_obj.user.id != user_id:
            raise DataSourceError(
                'Deletion Error',
                f'The linked {above_type} is not yours.',
                400
            )

        board_ds.delete(joiner_type, [joiner_obj.id])

    def delete(
        bigger_type: str,
        bigger_id: str,
        user_id: str
    ) -> None:
        """
        Given a bigger, containing object (e.g. `view`):

        - Deletes the sole join to an above object if one exists
          (here `board`). Raises a `DataSourceError` if either:
            1. the above object does not belong to the user
               calling this method.
            2. there is more than one above join (e.g. if this
               `zone` is in more than one `board`) regardless
               of user-ownership.
        - Recursively deletes all descendents (here
          `zone`->`component`), ending branching at any node
          that can't be deleted.
        - Deletes this bigger, containing object (here `view`).
        """

        bigger_obj = board_ds.get_one(bigger_type, bigger_id)

        if bigger_obj is None:
            raise DataSourceError(
                'Not Found',
                f'The given {bigger_type} was not found.',
                404
            )

        if bigger_obj.user.id != user_id:
            raise ForbiddenError()

        __delete_above(
            bigger_type,
            bigger_id,
            user_id
        )

        __delete_recursive(
            bigger_type,
            [bigger_obj],
            user_id
        )

    @board_bp.delete('/<string:object_type>/<string:object_id>')
    def __delete_endpoint(*, object_type: str, object_id: str):
        if object_type not in type_hierarchy:
            raise DataSourceError(
                'Unknown Type',
                'The given type is not recognised in the hierarchy',
                400
            )

        delete(
            object_type,
            object_id,
            ctx_getter().user_id
        )

        return {'deleted': True}, 200

    return board_bp
