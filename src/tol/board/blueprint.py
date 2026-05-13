# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from flask import Blueprint, request

from nanoid import generate

from .utils import (
    PREFIX_MAPPINGS,
    get_entity_type_from_prefix,
    collect_recursive,
    serialise_board_entities,
    get_parent_joiner_objs,
)
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

if TYPE_CHECKING:
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

    leaf_child_type = type_hierarchy[-1]
    root_parent_type = type_hierarchy[0]

    def __child_is_deletable(
        child_obj: DataObject,
        parent_type: str,
        all_parent_ids: list[str | None],
        joiner_type: str
    ) -> bool:
        """
        Reasons a child row can't be deleted:

        1. It doesn't belong to the user that
           is initiating the delete (managed by
           the calling function before this one).

          2. Other parent rows point to this child
              (e.g. this `zone` is in another `view`).
        """

        f = DataSourceFilter(
            and_={
                f'{parent_type}.id': {
                    'in_list': {
                        'value': all_parent_ids,
                        'negate': True
                    }
                },
                f'{child_obj.type}.id': {
                    'eq': {
                        'value': child_obj.id
                    }
                },
            }
        )
        count = board_ds.get_count(
            joiner_type,
            object_filters=f
        )

        return count == 0

    def __get_deletable_children(
        child_type: str,
        joiner_type: str,
        parent_type: str,
        all_parent_ids: list[str | None],
        joins: list[DataObject],
        user_id: str,
    ) -> list[DataObject]:
        """
        Given a parent->child relation (e.g.
        `zone` rows in a `view`) and the join
        rows that define it (e.g. `zone_view`),
        this function gets the child rows
        (here `zone`) that can be deleted.
        """

        all_child_objs: list[DataObject] = [
            getattr(join, child_type)
            for join in joins
        ]

        can_delete_any_owner = 'warden' in ctx_getter().roles

        return [
            obj for obj in all_child_objs
            if (can_delete_any_owner or getattr(obj.user, 'id', None) == user_id)
            and __child_is_deletable(
                obj,
                parent_type,
                all_parent_ids,
                joiner_type
            )
        ]

    def __delete_recursive(
        parent_type: str,
        parent_objs: list[DataObject],
        user_id: str
    ) -> None:
        """
        Given a list of parent, containing objects (e.g. `view`),
        deletes the contained objects (`zone`->`component`)
        recursively.

        Stops recursion within a branch in which its head can't
        be deleted.
        """

        all_parent_ids = [obj.id for obj in parent_objs]

        if parent_type != leaf_child_type:
            all_deletable_children = []
            all_join_ids = []

            parent_index = type_hierarchy.index(parent_type)
            child_type = type_hierarchy[parent_index + 1]
            joiner_type = f'{child_type}_{parent_type}'

            for parent_obj in parent_objs:
                joins_filter = DataSourceFilter(
                    and_={
                        f'{parent_obj.type}.id': {
                            'eq': {
                                'value': parent_obj.id
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

                deletable_children = __get_deletable_children(
                    child_type,
                    joiner_type,
                    parent_type,
                    all_parent_ids,
                    joins,
                    user_id,
                )
                all_deletable_children.extend(deletable_children)

                join_ids = [getattr(j, 'id', None) for j in joins]
                all_join_ids.extend(join_ids)

            # delete the joins first
            board_ds.delete(joiner_type, all_join_ids)

            __delete_recursive(child_type, all_deletable_children, user_id)

        board_ds.delete(parent_type, all_parent_ids)

    def __delete_above(
        object_type: str,
        object_id: str,
    ) -> None:
        """
        Deletes the (sole) joining table entry pointing to the specified
        `object_type`, if it's not the parent type (aka `board`).

        Fails if:
        - there is more than one joining entry (e.g. `zone_view` -> `zone`)
        - the (sole) joining entry does not belong to the authenticated user
        """

        if object_type == root_parent_type:
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

        board_ds.delete(joiner_type, [joiner_obj.id])

    def delete(
        parent_type: str,
        parent_id: str,
        user_id: str
    ) -> None:
        """
        Given a parent, containing object (e.g. `view`):

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
        - Deletes this parent, containing object (here `view`).
        """

        parent_obj = board_ds.get_one(parent_type, parent_id)

        if parent_obj is None:
            raise DataSourceError(
                'Not Found',
                f'The given {parent_type} was not found.',
                404
            )

        if getattr(parent_obj.user, 'id', None) != user_id and \
                'warden' not in ctx_getter().roles:
            raise ForbiddenError()

        __delete_above(
            parent_type,
            parent_id
        )

        __delete_recursive(
            parent_type,
            [parent_obj],
            user_id
        )

    def __save_board_entity_and_children(
        entities: dict[str, list[DataObject]],
        user_id: str,
        new_parent_title: str,
        parent_type: str,
        object_type: str = root_parent_type,
        parent_id: str | None = None,
    ) -> tuple[str, dict[str, str]]:
        """
        Saves the given entities and their relations to the database.

        Expects the entities to be in a dict keyed by type (including
        joiner types) mapping to the list of `DataObject`s of that type,
        as returned by `collect_recursive`.
        """

        custom_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        prefix_mappings = {
            'board': 'b',
            'view': 'v',
            'zone': 'z',
            'component': 'c',
        }

        # Build old -> new ID mapping for all non-joiner types
        id_mapping: dict[str, str] = {}
        for entity_type, objs in entities.items():
            if entity_type in type_hierarchy:
                for obj in objs:
                    new_id = (
                        f'{prefix_mappings.get(entity_type, "x")}'
                        f'_{generate(custom_alphabet, 12)}'
                    )
                    id_mapping[obj.id] = new_id

        for entity_type in type_hierarchy:
            for obj in entities.get(entity_type, []):
                original_user = obj.to_one_relationships.get('user')
                user_stub = board_ds.data_object_factory(
                    type_=original_user.type if original_user else 'user',
                    id_=user_id,
                )
                to_one = {
                    rel_name: (user_stub if rel_name == 'user' else rel_obj)
                    for rel_name, rel_obj in obj.to_one_relationships.items()
                }
                new_obj = board_ds.data_object_factory(
                    type_=entity_type,
                    id_=id_mapping[obj.id],
                    attributes=(
                        {**obj.attributes, 'title': new_parent_title}
                        if entity_type == 'board'
                        else obj.attributes
                    ),
                    to_one=to_one,
                )
                board_ds.insert(entity_type, [new_obj])

        for entity_type, objs in entities.items():
            if entity_type not in type_hierarchy:
                parent_t = next(t for t in type_hierarchy if entity_type.endswith(f'_{t}'))
                child_t = entity_type[: -(len(parent_t) + 1)]
                for obj in objs:
                    child_obj = getattr(obj, child_t)
                    parent_obj = getattr(obj, parent_t)
                    new_obj = board_ds.data_object_factory(
                        type_=entity_type,
                        attributes={'order': obj.order},
                        to_one={
                            child_t: board_ds.data_object_factory(
                                type_=child_t,
                                id_=id_mapping[child_obj.id],
                            ),
                            parent_t: board_ds.data_object_factory(
                                type_=parent_t,
                                id_=id_mapping[parent_obj.id],
                            ),
                        },
                    )
                    board_ds.insert(entity_type, [new_obj])

        if parent_id is not None:
            joiner_type = f'{object_type}_{parent_type}'
            num_parent_joins = board_ds.get_count(
                joiner_type,
                object_filters=DataSourceFilter(
                    and_={
                        f'{parent_type}.id': {
                            'eq': {
                                'value': parent_id
                            }
                        }
                    }
                )
            )
            new_root_id = id_mapping[entities[object_type][0].id]
            joiner_obj = board_ds.data_object_factory(
                type_=joiner_type,
                attributes={'order': num_parent_joins + 1},
                to_one={
                    object_type: board_ds.data_object_factory(
                        type_=object_type,
                        id_=new_root_id,
                    ),
                    parent_type: board_ds.data_object_factory(
                        type_=parent_type,
                        id_=parent_id,
                    ),
                },
            )
            board_ds.insert(joiner_type, [joiner_obj])

        return id_mapping[entities[object_type][0].id], id_mapping

    @board_bp.post('/copy/<string:object_type>/<string:object_id>')
    def __copy_entity(*, object_type: str, object_id: str):
        obj = board_ds.get_one(object_type, object_id)
        if obj is None or obj.id is None:
            raise DataSourceError(
                'Not Found',
                f'The given {object_type} was not found.',
                404
            )

        new_parent_title = request.json.get(
            'new_parent_entity_title', f'{obj.title} - copy')
        parent_type = request.json.get('parent_entity_type', 'board')
        parent_id = request.json.get('parent_entity_id')

        all_entities = collect_recursive(board_ds, object_type, [obj], type_hierarchy)
        new_entity_id, id_mapping = __save_board_entity_and_children(
            all_entities, ctx_getter().user_id, new_parent_title,
            parent_type, object_type, parent_id)

        if not all_entities.get(object_type) or not new_entity_id:
            raise DataSourceError(
                'Copy Error',
                f'An error occurred while copying the {object_type}.',
                500
            )

        copied_entity = serialise_board_entities(all_entities, obj.id, type_hierarchy, id_mapping)
        copied_entity['title'] = new_parent_title

        return copied_entity, 201

    @board_bp.post('/add-entity/<string:object_type>/<string:parent_id>')
    def __add_entity_endpoint(*, object_type: str, parent_id: str):
        if object_type not in type_hierarchy:
            raise DataSourceError(
                'Unknown Type',
                'The given type is not recognised in the hierarchy',
                400
            )

        object_index = type_hierarchy.index(object_type)
        if object_index == 0:
            raise DataSourceError(
                'Add Error',
                f'Cannot add {object_type} with a parent ID.',
                400
            )

        expected_parent_type = type_hierarchy[object_index - 1]
        parent_type = get_entity_type_from_prefix(parent_id.split('_', 1)[0])
        if parent_type is None or parent_type != expected_parent_type:
            raise DataSourceError(
                'Bad Parent',
                f'The parent ID does not match expected type {expected_parent_type}.',
                400
            )

        parent_obj = board_ds.get_one(parent_type, parent_id)
        if parent_obj is None or parent_obj.id is None:
            raise DataSourceError(
                'Not Found',
                f'The given {parent_type} was not found.',
                404
            )

        ctx = ctx_getter()
        if getattr(parent_obj.user, 'id', None) != ctx.user_id and 'warden' not in ctx.roles:
            raise ForbiddenError()

        payload = request.json or {}
        attributes = payload.get('attributes', {})

        if 'title' not in attributes:
            attributes['title'] = f'New {object_type}'

        if object_type in ('board', 'view', 'zone', 'component') and 'filter' not in attributes:
            attributes['filter'] = {}

        id_prefix = object_type[:1]
        custom_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        new_entity_id = f'{id_prefix}_{generate(custom_alphabet, 12)}'

        user_stub = board_ds.data_object_factory(
            type_='user',
            id_=ctx.user_id,
        )

        new_entity = board_ds.data_object_factory(
            type_=object_type,
            id_=new_entity_id,
            attributes=attributes,
            to_one={'user': user_stub},
        )
        board_ds.insert(object_type, [new_entity])

        joiner_type = f'{object_type}_{parent_type}'
        joins_filter = DataSourceFilter(
            and_={
                f'{parent_type}.id': {
                    'eq': {
                        'value': parent_id
                    }
                }
            }
        )
        existing_joins = list(board_ds.get_list(joiner_type, object_filters=joins_filter))
        next_order = max((getattr(join, 'order', 0) for join in existing_joins), default=0) + 1

        join_obj = board_ds.data_object_factory(
            type_=joiner_type,
            attributes={'order': next_order},
            to_one={
                object_type: board_ds.data_object_factory(
                    type_=object_type,
                    id_=new_entity_id,
                ),
                parent_type: board_ds.data_object_factory(
                    type_=parent_type,
                    id_=parent_id,
                ),
            },
        )
        board_ds.insert(joiner_type, [join_obj])

        return {
            'id': new_entity_id,
            'type': object_type,
            'parent_id': parent_id,
            'order': next_order,
            **attributes,
        }, 201

    @board_bp.post('/create-board')
    def __create_board_endpoint():
        payload = request.json or {}
        board_title = payload.get('board_title', 'New board')
        first_view_title = payload.get('first_view_title', 'View 1')

        board_type = type_hierarchy[0]
        view_type = type_hierarchy[1]

        custom_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        board_prefix = PREFIX_MAPPINGS.get(board_type, board_type[:1].lower())
        board_id = f'{board_prefix}_{generate(custom_alphabet, 12)}'

        user_stub = board_ds.data_object_factory(
            type_='user',
            id_=ctx_getter().user_id,
        )

        board_obj = board_ds.data_object_factory(
            type_=board_type,
            id_=board_id,
            attributes={
                'title': board_title,
                'filter': {},
            },
            to_one={'user': user_stub},
        )
        board_ds.insert(board_type, [board_obj])

        # Add the first view using add_entity logic
        view_attributes = {
            'title': first_view_title,
            'filter': {},
        }

        view_id_prefix = PREFIX_MAPPINGS.get(view_type, view_type[:1].lower())
        view_id = f'{view_id_prefix}_{generate(custom_alphabet, 12)}'

        view_obj = board_ds.data_object_factory(
            type_=view_type,
            id_=view_id,
            attributes=view_attributes,
            to_one={'user': user_stub},
        )
        board_ds.insert(view_type, [view_obj])

        joiner_type = f'{view_type}_{board_type}'
        joins_filter = DataSourceFilter(
            and_={
                f'{board_type}.id': {
                    'eq': {
                        'value': board_id
                    }
                }
            }
        )
        existing_joins = list(board_ds.get_list(joiner_type, object_filters=joins_filter))
        next_order = max((getattr(join, 'order', 0) for join in existing_joins), default=0) + 1

        view_board_obj = board_ds.data_object_factory(
            type_=joiner_type,
            attributes={'order': next_order},
            to_one={
                view_type: board_ds.data_object_factory(
                    type_=view_type,
                    id_=view_id,
                ),
                board_type: board_ds.data_object_factory(
                    type_=board_type,
                    id_=board_id,
                ),
            },
        )
        board_ds.insert(joiner_type, [view_board_obj])

        # Return full serialized board JSON
        entities = {
            board_type: [board_obj],
            view_type: [view_obj],
            joiner_type: [view_board_obj],
        }
        serialised = serialise_board_entities(entities, board_id, type_hierarchy)

        return serialised, 201

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


    def reorder(
        parent_object_id: str,
        new_order: list[str]
    ) -> None:
        """
        Reorders child entities under a given parent entity.

        Expects a list of child entity IDs in the desired order.

        Validates that the provided order includes all and only the actual child IDs.
        """

        parent_object_type = get_entity_type_from_prefix(parent_object_id.split('_', 1)[0])
        child_object_type = get_entity_type_from_prefix(new_order[0].split('_', 1)[0])
        joiner_object_type = f'{child_object_type}_{parent_object_type}'

        # Getting the actual child IDs from the given parent
        joiner_objs = get_parent_joiner_objs(
            board_ds,
            parent_object_id,
            joiner_object_type
        )
        actual_child_ids = [
            obj.to_one_relationships[child_object_type].id
            for obj in joiner_objs
        ]

        # Ensure the new order includes all and only the child IDs
        if len(actual_child_ids) != len(new_order) or set(actual_child_ids) != set(new_order):
            raise DataSourceError(
                'Invalid Order',
                'Not all child IDs are included '
                'in the new order, or there are '
                'extra IDs that are not children.',

                400
            )

        # Build a lookup of child ID -> joiner object, which we can use to
        # create the updated joiner objects with the new order values
        joiner_ids_by_child_id = {
            obj.to_one_relationships[child_object_type].id: obj.id
            for obj in joiner_objs
        }

        # Create new joiner objects with the updated order values
        updated_joiners = [
            board_ds.data_object_factory(
                type_=joiner_object_type,
                id_=joiner_ids_by_child_id[child_id],
                attributes={'order': order},
            )
            for order, child_id in enumerate(new_order)
        ]

        board_ds.upsert(joiner_object_type, updated_joiners)

    @board_bp.patch('/reorder/<string:parent_object_id>')
    def __reorder_endpoint(*, parent_object_id: str):
        """
        Reorders child entities under a given parent entity.

        Expects a JSON body with an 'order' field containing a
        list of child entity IDs in the desired order.

        Validates that the provided order includes all and only the actual child IDs.
        """
        new_order = request.json.get('order')

        reorder(parent_object_id, new_order)

        # Use the passed order as the reorder function already validates
        return {
            'order': new_order
        }, 200

    @board_bp.get('/get-entity/<string:object_type>/<string:object_id>')
    def __get_board_entities(*, object_type: str, object_id: str):
        obj = board_ds.get_one(object_type, object_id)
        if obj is None or obj.id is None:
            raise DataSourceError(
                'Not Found',
                f'The given {object_type} was not found.',
                404
            )

        all_entities = collect_recursive(board_ds, object_type, [obj], type_hierarchy)
        serialised_entities = serialise_board_entities(all_entities, obj.id, type_hierarchy, id_mapping=None)

        return serialised_entities, 200

    return board_bp
