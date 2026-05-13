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
    save_board_entity_and_children,
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

    smallest_type = type_hierarchy[-1]
    biggest_type = type_hierarchy[0]

    def __smaller_is_deletable(
        smaller_obj: DataObject,
        bigger_type: str,
        all_bigger_ids: list[str | None],
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
        all_bigger_ids: list[str | None],
        joins: list[DataObject],
        user_id: str,
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

        can_delete_any_owner = 'warden' in ctx_getter().roles

        return [
            obj for obj in all_smaller_objs
            if (can_delete_any_owner or getattr(obj.user, 'id', None) == user_id)
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
                    user_id,
                )
                all_deletable_smallers.extend(deletable_smallers)

                join_ids = [getattr(j, 'id', None) for j in joins]
                all_join_ids.extend(join_ids)

            # delete the joins first
            board_ds.delete(joiner_type, all_join_ids)

            __delete_recursive(smaller_type, all_deletable_smallers, user_id)

        board_ds.delete(bigger_type, all_bigger_ids)

    def __delete_above(
        object_type: str,
        object_id: str,
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

        if getattr(bigger_obj.user, 'id', None) != user_id and \
                'warden' not in ctx_getter().roles:
            raise ForbiddenError()

        __delete_above(
            bigger_type,
            bigger_id
        )

        __delete_recursive(
            bigger_type,
            [bigger_obj],
            user_id
        )

    def __collect_recursive(
        bigger_type: str,
        bigger_objs: list[DataObject],
        collected: dict[str, list[DataObject]] | None = None,
    ) -> dict[str, list[DataObject]]:
        """
        Given a list of bigger, containing objects (e.g. `view`),
        recursively collects all contained objects and their join
        rows without ownership filtering.

        Returns a dict keyed by type (including joiner types) mapping
        to the list of `DataObject`s of that type, suitable for passing
        back to a caller that wants to recreate the full hierarchy (e.g.
        for a board-copy operation).
        """

        if collected is None:
            collected = {}

        collected.setdefault(bigger_type, []).extend(bigger_objs)

        if bigger_type == smallest_type:
            return collected

        bigger_index = type_hierarchy.index(bigger_type)
        child_type = type_hierarchy[bigger_index + 1]
        joiner_type = f'{child_type}_{bigger_type}'

        all_joins: list[DataObject] = []
        all_child_objs: list[DataObject] = []

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
            all_joins.extend(joins)
            all_child_objs.extend(
                getattr(join, child_type) for join in joins
            )

        collected.setdefault(joiner_type, []).extend(all_joins)

        if all_child_objs:
            __collect_recursive(child_type, all_child_objs, collected)

        return collected

    def __serialise_board_entities(
        parent_id: str,
        all_entities: dict[str, list[DataObject]],
        id_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        serialises the given entities into a nested dict structure suitable
        for consumption by the frontend, starting at the given parent ID and
        type (e.g. a `view` ID and `view` type would serialise that
        view along with its child zones and components).
        """

        # We loop through the joiner types (e.g. `zone_view`) to build a lookup of parent ID
        # (e.g. `view` ID) -> list of child IDs (e.g. `zone` IDs),
        # which we can use when serializing the children of each object
        children_lookup: dict[str, list[str]] = {}

        for entity_type, objs in all_entities.items():
            if entity_type not in type_hierarchy:
                bigger_type = next(t for t in type_hierarchy if entity_type.endswith(f'_{t}'))
                smaller_type = entity_type[: -(len(bigger_type) + 1)]
                for obj in sorted(objs, key=lambda o: getattr(o, 'order', 0)):
                    bigger_obj = getattr(obj, bigger_type)
                    smaller_obj = getattr(obj, smaller_type)
                    children_lookup.setdefault(bigger_obj.id, []).append(smaller_obj.id)

        # We loop through the non-joiner types to build a lookup of ID -> object,
        # which we can use when serializing the children of each object
        obj_lookup: dict[str, DataObject] = {
            str(obj.id): obj
            for entity_type, objs in all_entities.items()
            if entity_type in type_hierarchy
            for obj in objs
        }

        # We define a recursive serialization function that uses the above
        # lookups to serialise each object along with its children
        def _serialise(obj: DataObject) -> dict[str, Any]:
            obj_id: str = str(obj.id)
            mapped_id: str = id_mapping.get(obj_id, obj_id) if id_mapping else obj_id

            child_ids: list[str] = children_lookup.get(obj_id, [])
            mapped_child_ids: list[str] = [id_mapping.get(child_id, child_id)
                                           for child_id in child_ids] if id_mapping else child_ids

            result: dict[str, Any] = {
                'id': mapped_id,
                'type': obj.type,
                # We filter out the 'filter' attribute for non-component and non-zone types,
                # as it isn't currently needed, can re-add later when needed, i.e. param boards
                **{
                    k: v for k, v in obj.attributes.items()
                    if k != 'filter' or obj.type in ('component', 'zone')
                },
            }

            # Component is the only type that doesn't have an 'order' field
            # in the joiner table, nor does it have any child entities, so we
            # can skip adding the 'order' and 'children' fields for it
            if obj.type != 'component':
                result['order'] = mapped_child_ids
                result['children'] = {
                    mapped_child_id: _serialise(obj_lookup[child_id])
                    for child_id, mapped_child_id in zip(child_ids, mapped_child_ids)
                    if child_id in obj_lookup
                },

            if obj.type == 'zone' or obj.type == 'component':
                result['data_source_instance_id'] = getattr(
                    obj.data_source_instance, 'id', None)
                result['ui_api_details'] = getattr(
                    obj.data_source_instance, 'ui_api_details', None)

            if obj.type == 'board':
                result['owner_email'] = getattr(obj.user, 'oidc_id', None)
                ctx = ctx_getter()
                result['write_privilege'] = (
                    ctx.authenticated
                    and (getattr(obj.user, 'id', None) == ctx.user_id or 'warden' in ctx.roles)
                )

            if obj.type == 'component':
                user_config = list(board_ds.get_list(
                    'board_diff',
                    object_filters=DataSourceFilter(
                        and_={
                            'component_id': {
                                'eq': {
                                    'value': obj.id
                                }
                            },
                            'user_id': {
                                'eq': {
                                    'value': ctx_getter().user_id
                                }
                            }
                        }
                    )
                )) if ctx_getter().authenticated else []
                result['config_diff'] = {
                    'id': getattr(user_config[0], 'id', None) if user_config else None,
                    'config': getattr(user_config[0], 'config', None) if user_config else None
                }

            return result

        # We start the recursive serialization at the given parent ID and type
        parent_obj = obj_lookup.get(parent_id)
        if parent_obj is None:
            return {}

        return _serialise(parent_obj)

    def __save_board_entity_and_children(
        entities: dict[str, list[DataObject]],
        user_id: str,
        new_parent_title: str,
        parent_type: str,
    ) -> tuple[str, dict[str, str]]:
        """
        Saves the given entities and their relations to the database.

        Expects the entities to be in a dict keyed by type (including
        joiner types) mapping to the list of `DataObject`s of that type,
        as returned by `__collect_recursive`.
        """
        return save_board_entity_and_children(
            board_ds=board_ds,
            entities=entities,
            user_id=user_id,
            new_parent_title=new_parent_title,
            parent_type=parent_type,
            type_hierarchy=type_hierarchy,
        )

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

        all_entities = __collect_recursive(object_type, [obj])
        new_entity_id, id_mapping = __save_board_entity_and_children(
            all_entities, ctx_getter().user_id, new_parent_title, parent_type)

        if not all_entities.get(object_type) or not new_entity_id:
            raise DataSourceError(
                'Copy Error',
                f'An error occurred while copying the {object_type}.',
                500
            )

        copied_entity = __serialise_board_entities(obj.id, all_entities, id_mapping)
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
        serialised = __serialise_board_entities(board_id, entities)

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

    @board_bp.get('/get-entity/<string:object_type>/<string:object_id>')
    def __get_board_entities(*, object_type: str, object_id: str):
        obj = board_ds.get_one(object_type, object_id)
        if obj is None or obj.id is None:
            raise DataSourceError(
                'Not Found',
                f'The given {object_type} was not found.',
                404
            )

        all_entities = __collect_recursive(object_type, [obj])
        serialised_entities = __serialise_board_entities(obj.id, all_entities, id_mapping=None)

        return serialised_entities, 200

    return board_bp
