# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, request
from nanoid import generate

from .errors import (
    AddError,
    BadParentError,
    CopyError,
    DeletionError,
    InvalidOrderError,
    NotFoundError,
    UnknownTypeError,
)
from .utils import (
    collect_recursive,
    generate_entity_id,
    get_entity_type_from_prefix,
    get_parent_joiner_objs,
    save_board_entity_and_children,
    serialise_board_entities,
)
from ..api_base.auth import ForbiddenError
from ..api_base.misc import (
    CtxGetter,
    default_ctx_getter
)
from ..core import (
    DataObject,
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
        all_parent_ids: list[str],
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
        all_parent_ids: list[str],
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

        all_parent_ids = [obj.id for obj in parent_objs if obj.id is not None]

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

                join_ids = [j.id for j in joins if getattr(j, 'id', None) is not None]
                all_join_ids.extend(join_ids)

            # delete the joins first
            board_ds.delete(joiner_type, all_join_ids)

            __delete_recursive(child_type, all_deletable_children, user_id)

        if all_parent_ids:
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
            raise DeletionError(above_type, object_type)

        (joiner_obj,) = list(
            board_ds.get_list(
                joiner_type,
                object_filters=f
            )
        )

        if joiner_obj.id is None:
            return

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
            raise NotFoundError(parent_type)

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

    @board_bp.post('/copy/<string:object_type>/<string:object_id>')
    def __copy_entity(*, object_type: str, object_id: str):
        obj = board_ds.get_one(object_type, object_id)
        if obj is None or obj.id is None:
            raise NotFoundError(object_type)

        payload = request.json or {}
        new_parent_title = payload.get('new_parent_entity_title', f'{obj.title} - copy')
        parent_type = str(payload.get('parent_entity_type', 'board'))
        raw_parent_id = payload.get('parent_entity_id')
        parent_id = str(raw_parent_id) if raw_parent_id is not None else None

        all_entities = collect_recursive(board_ds, object_type, [obj], type_hierarchy)
        new_entity_id, id_mapping = save_board_entity_and_children(
            board_ds,
            all_entities,
            ctx_getter().user_id,
            new_parent_title,
            parent_type,
            type_hierarchy,
            object_type=object_type,
            parent_id=parent_id,
            id_generator=generate,
        )

        if not all_entities.get(object_type) or not new_entity_id:
            raise CopyError(object_type)

        copied_entity = serialise_board_entities(all_entities, obj.id, type_hierarchy, id_mapping)
        copied_entity['title'] = new_parent_title

        return copied_entity, 201

    @board_bp.post('/add-entity/<string:object_type>/<string:parent_id>')
    def __add_entity_endpoint(*, object_type: str, parent_id: str):
        if object_type not in type_hierarchy:
            raise UnknownTypeError()

        object_index = type_hierarchy.index(object_type)
        if object_index == 0:
            raise AddError(object_type)

        expected_parent_type = type_hierarchy[object_index - 1]
        parent_type = get_entity_type_from_prefix(parent_id.split('_', 1)[0])
        if parent_type is None or parent_type != expected_parent_type:
            raise BadParentError(expected_parent_type)

        parent_obj = board_ds.get_one(parent_type, parent_id)
        if parent_obj is None or parent_obj.id is None:
            raise NotFoundError(parent_type)

        ctx = ctx_getter()
        if getattr(parent_obj.user, 'id', None) != ctx.user_id and 'warden' not in ctx.roles:
            raise ForbiddenError()

        payload = request.json or {}
        attributes = payload.get('attributes', {})

        if 'title' not in attributes:
            attributes['title'] = f'New {object_type}'

        if object_type in ('board', 'view', 'zone', 'component') and 'filter' not in attributes:
            attributes['filter'] = {}

        new_entity_id = generate_entity_id(
            object_type,
            id_generator=generate,
            fallback_prefix=object_type[:1],
        )

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

        serialised_entity = serialise_board_entities(
            {object_type: [new_entity]},
            new_entity_id,
            type_hierarchy,
        )

        if not serialised_entity:
            serialised_entity = {
                'id': new_entity_id,
                'type': object_type,
                **{
                    k: v for k, v in attributes.items()
                    if k != 'filter' or object_type in ('component', 'zone')
                },
            }
            if object_type != 'component':
                serialised_entity['order'] = []
                serialised_entity['children'] = {}

        return {
            **serialised_entity,
            'parent_id': parent_id,
            'parent_order': next_order,
        }, 201

    @board_bp.post('/create-board')
    def __create_board_endpoint():
        payload = request.json or {}
        board_title = payload.get('board_title', 'Untitled board')
        first_view_title = payload.get('first_view_title', 'View 1')

        board_type = type_hierarchy[0]
        view_type = type_hierarchy[1]

        board_id = generate_entity_id(board_type, id_generator=generate)

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

        view_id = generate_entity_id(view_type, id_generator=generate)

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
            raise UnknownTypeError()

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

        parent_prefix = parent_object_id.split('_', 1)[0]
        parent_object_type = get_entity_type_from_prefix(parent_prefix) or parent_prefix

        if not new_order:
            raise InvalidOrderError()

        child_prefix = new_order[0].split('_', 1)[0]
        child_object_type = get_entity_type_from_prefix(child_prefix) or child_prefix

        joiner_object_type = f'{child_object_type}_{parent_object_type}'

        # Getting the actual child IDs from the given parent
        joiner_objs = get_parent_joiner_objs(
            board_ds,
            parent_object_id,
            joiner_object_type
        )
        actual_child_ids: list[str] = []
        for obj in joiner_objs:
            child_rel = obj.to_one_relationships.get(child_object_type)
            child_id = getattr(child_rel, 'id', None)
            if child_id is None:
                raise InvalidOrderError()
            actual_child_ids.append(child_id)

        # Ensure the new order includes all and only the child IDs
        if len(actual_child_ids) != len(new_order) or set(actual_child_ids) != set(new_order):
            raise InvalidOrderError()

        # Build a lookup of child ID -> joiner object, which we can use to
        # create the updated joiner objects with the new order values
        joiner_ids_by_child_id: dict[str, str] = {}
        for obj in joiner_objs:
            child_rel = obj.to_one_relationships.get(child_object_type)
            child_id = getattr(child_rel, 'id', None)
            joiner_id = getattr(obj, 'id', None)
            if child_id is None or joiner_id is None:
                raise InvalidOrderError()
            joiner_ids_by_child_id[child_id] = joiner_id

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
        payload = request.json or {}
        new_order = payload.get('order')

        if not isinstance(new_order, list) or not all(isinstance(item, str) for item in new_order):
            raise InvalidOrderError()

        reorder(parent_object_id, new_order)

        # Use the passed order as the reorder function already validates
        return {
            'order': new_order
        }, 200

    @board_bp.get('/get-entity/<string:object_type>/<string:object_id>')
    def __get_board_entities(*, object_type: str, object_id: str):
        obj = board_ds.get_one(object_type, object_id)
        if obj is None or obj.id is None:
            raise NotFoundError(object_type)

        all_entities = collect_recursive(board_ds, object_type, [obj], type_hierarchy)
        serialised_entities = serialise_board_entities(
            all_entities, obj.id, type_hierarchy, id_mapping=None
        )

        return serialised_entities, 200

    return board_bp
