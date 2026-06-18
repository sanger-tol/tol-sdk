# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from nanoid import generate

from tol.api_base.auth.error import ForbiddenError
from tol.board.errors import PayloadError

from .constants import CUSTOM_ID_ALPHABET, PREFIX_MAPPINGS, TYPE_HIERARCHY
from ..api_base.misc import CtxGetter, default_ctx_getter
from ..core import DataObject, DataSourceFilter

if TYPE_CHECKING:
    from ..sql import SqlDataSource


def generate_entity_id(
    entity_type: str,
    fallback_prefix: str | None = None,
) -> str:
    """
    Generates a prefixed entity ID (e.g. `b_xxxxxxxxxxxx`).

    Args:
        entity_type: The entity type (e.g. 'board', 'view', 'zone', 'component')

    Returns:
        A generated entity ID with the mapped prefix.
    """

    fallback_prefix = fallback_prefix or entity_type[:1].lower()
    prefix = PREFIX_MAPPINGS.get(entity_type, fallback_prefix)
    return f'{prefix}_{generate(CUSTOM_ID_ALPHABET, 12)}'


def get_entity_and_child_type_from_parent_id(parent_id: str) -> tuple[str, str | None]:
    """
    Returns the entity type corresponding to the given prefix.

    Args:
        parent_id: The ID of the parent entity (e.g., 'b_123456789012')

    Returns:
        The entity type string (e.g., 'board', 'view', 'zone', 'component'),
        or None if the prefix is not recognized.

    Examples:
        >>> get_entity_and_child_type_from_parent_id('b_123456789012')
        ('board', 'view')
        >>> get_entity_and_child_type_from_parent_id('v_123456789012')
        ('view', 'zone')
        >>> get_entity_and_child_type_from_parent_id('x_123456789012')
        (None, None)
    """

    reverse_mappings = {v: k for k, v in PREFIX_MAPPINGS.items()}

    prefix = parent_id.split('_', 1)[0]
    parent_type = reverse_mappings.get(prefix)

    if parent_type is None:
        raise ValueError(f'Unrecognized parent ID prefix: {prefix}')

    parent_index = TYPE_HIERARCHY.index(parent_type)
    child_type = TYPE_HIERARCHY[parent_index + 1] \
        if parent_index + 1 < len(TYPE_HIERARCHY) else None

    return parent_type, child_type


def save_board_entity_and_children(
    board_ds: SqlDataSource,
    entities: dict[str, list[DataObject]],
    user_id: str,
    new_parent_title: str,
    parent_type: str,
    object_type: str | None = None,
    parent_id: str | None = None,
) -> tuple[str, dict[str, str]]:
    """
    Saves the given entities and their relations to the database.

    Expects the entities to be in a dict keyed by type (including
    joiner types) mapping to the list of `DataObject`s of that type,
    as returned by `__collect_recursive`.

    Args:
        board_ds: The data source for board operations
        entities: Dict mapping entity types to lists of DataObjects
        user_id: The ID of the user owning the entities
        new_parent_title: Title for the parent entity
        parent_type: The type of the parent entity
        type_hierarchy: The hierarchy of entity types
        object_type: The root copied object type; defaults to the hierarchy root
        parent_id: Optional parent object ID to attach copied root to
        id_generator: Callable used to generate random ID suffixes

    Returns:
        A tuple of (new_parent_entity_id, id_mapping) where id_mapping
        maps old IDs to newly generated IDs
    """

    root_parent_type = TYPE_HIERARCHY[0]
    object_type = object_type or root_parent_type

    # Build old -> new ID mapping for all non-joiner types
    id_mapping: dict[str, str] = {}
    with board_ds.get_session() as session:
        for entity_type, objs in entities.items():
            if entity_type in TYPE_HIERARCHY:
                for obj in objs:
                    if obj.id is None:
                        continue
                    id_mapping[obj.id] = generate_entity_id(entity_type)

        for entity_type in TYPE_HIERARCHY:
            for obj in entities.get(entity_type, []):
                if obj.id is None or obj.id not in id_mapping:
                    continue
                original_user = obj.to_one_relationships.get('user')
                user_stub = session.data_object_factory(
                    type_=original_user.type if original_user else 'user',
                    id_=user_id,
                )
                to_one = {
                    rel_name: (user_stub if rel_name == 'user' else rel_obj)
                    for rel_name, rel_obj in obj.to_one_relationships.items()
                }
                new_obj = session.data_object_factory(
                    type_=entity_type,
                    id_=id_mapping[obj.id],
                    attributes={
                        **obj.attributes, 'title': new_parent_title}
                    if entity_type == root_parent_type else obj.attributes,
                    to_one=to_one,
                )
                session.insert(entity_type, [new_obj])

        for entity_type, objs in entities.items():
            if entity_type not in TYPE_HIERARCHY:
                parent_t = next(t for t in TYPE_HIERARCHY if entity_type.endswith(f'_{t}'))
                child_t = entity_type[: -(len(parent_t) + 1)]
                for obj in objs:
                    child_obj = getattr(obj, child_t)
                    parent_obj = getattr(obj, parent_t)
                    if child_obj.id is None or parent_obj.id is None:
                        continue
                    if child_obj.id not in id_mapping or parent_obj.id not in id_mapping:
                        continue
                    new_obj = session.data_object_factory(
                        type_=entity_type,
                        attributes={'order': obj.order},
                        to_one={
                            child_t: session.data_object_factory(
                                type_=child_t,
                                id_=id_mapping[child_obj.id],
                            ),
                            parent_t: session.data_object_factory(
                                type_=parent_t,
                                id_=id_mapping[parent_obj.id],
                            ),
                        },
                    )
                    session.insert(entity_type, [new_obj])

        root_objects = entities.get(object_type, [])
        root_source_id = next(
            (obj.id for obj in root_objects if obj.id is not None and obj.id in id_mapping),
            None,
        )
        if root_source_id is None:
            raise ValueError(f'No valid root object found for {object_type}')

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
            new_root_id = id_mapping[root_source_id]
            joiner_obj = session.data_object_factory(
                type_=joiner_type,
                attributes={'order': num_parent_joins + 1},
                to_one={
                    object_type: session.data_object_factory(
                        type_=object_type,
                        id_=new_root_id,
                    ),
                    parent_type: session.data_object_factory(
                        type_=parent_type,
                        id_=parent_id,
                    ),
                },
            )
            session.insert(joiner_type, [joiner_obj])

    return id_mapping[root_source_id], id_mapping


def collect_recursive(
    board_ds: SqlDataSource,
    object_type: str,
    parent_objs: list[DataObject],
    collected: dict[str, list[DataObject]] | None = None,
) -> dict[str, list[DataObject]]:
    """
    Recursively collects all contained objects and their join rows
    without ownership filtering.

    Returns a dict keyed by type (including joiner types) mapping
    to the list of `DataObject`s of that type, suitable for passing
    back to a caller that wants to recreate the full hierarchy.

    Args:
        board_ds: The data source for board operations
        object_type: The current object type being processed
        parent_objs: List of containing objects
        type_hierarchy: The hierarchy of entity types
        collected: Accumulation dict for recursion

    Returns:
        Dict mapping entity types to lists of DataObjects
    """

    if collected is None:
        collected = {}

    leaf_child_type = TYPE_HIERARCHY[-1]

    collected.setdefault(object_type, []).extend(parent_objs)

    if object_type == leaf_child_type:
        return collected

    parent_index = TYPE_HIERARCHY.index(object_type)
    child_type = TYPE_HIERARCHY[parent_index + 1]
    joiner_type = f'{child_type}_{object_type}'

    all_joins: list[DataObject] = []
    all_child_objs: list[DataObject] = []

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
        all_joins.extend(joins)
        all_child_objs.extend(
            getattr(join, child_type) for join in joins
        )

    collected.setdefault(joiner_type, []).extend(all_joins)

    if all_child_objs:
        collect_recursive(board_ds, child_type, all_child_objs, collected)

    return collected


def serialise_board_entities(
    all_entities: dict[str, list[DataObject]],
    parent_id: str,
    board_ds: SqlDataSource,
    id_mapping: dict[str, str] | None = None,
    ctx_getter: CtxGetter = default_ctx_getter,
) -> dict[str, Any]:
    """
    Serialises the given entities into a nested dict structure suitable
    for consumption by the frontend.

    Args:
        all_entities: Dict mapping entity types to lists of DataObjects
        parent_id: The ID of the parent entity to start serialization from
        type_hierarchy: The hierarchy of entity types
        id_mapping: Optional mapping of old IDs to new IDs
        board_ds: The data source for board operations
        ctx_getter: Function to get the current context

    Returns:
        Nested dict structure representing the entities
    """

    # We loop through the joiner types (e.g. `zone_view`) to build a lookup of parent ID
    # (e.g. `view` ID) -> list of child IDs (e.g. `zone` IDs),
    # which we can use when serializing the children of each object
    children_lookup: dict[str, list[str]] = {}

    for entity_type, objs in all_entities.items():
        if entity_type not in TYPE_HIERARCHY:
            parent_type = next(t for t in TYPE_HIERARCHY if entity_type.endswith(f'_{t}'))
            child_type = entity_type[: -(len(parent_type) + 1)]
            for obj in sorted(objs, key=lambda o: getattr(o, 'order', 0)):
                parent_obj = getattr(obj, parent_type)
                child_obj = getattr(obj, child_type)
                children_lookup.setdefault(parent_obj.id, []).append(child_obj.id)

    # We loop through the non-joiner types to build a lookup of ID -> object,
    # which we can use when serializing the children of each object
    obj_lookup: dict[str, DataObject] = {
        str(obj.id): obj
        for entity_type, objs in all_entities.items()
        if entity_type in TYPE_HIERARCHY
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
            }

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
                'entity_diff',
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


def get_parent_joiner_objs(
    board_ds: SqlDataSource,
    parent_object_id: str,
    joiner_object_type: str,
) -> list[DataObject]:
    """
    Retrieves the joiner objects for a given parent object.

    Args:
        board_ds: The data source for board operations
        parent_object_id: The ID of the parent object
        joiner_object_type: The joiner type (e.g., 'zone_view')

    Returns:
        List of joiner DataObjects
    """

    parent_object_type = joiner_object_type.split('_')[1]
    f = DataSourceFilter(
        and_={
            f'{parent_object_type}.id': {
                'eq': {
                    'value': parent_object_id
                }
            }
        }
    )
    return list(board_ds.get_list(
        joiner_object_type,
        object_filters=f
    ))


def check_auth_and_required_fields(
    ctx_getter: CtxGetter,
    payload: dict[str, Any],
    required_fields: list[str] | None = None,
    owner_id: str | None = None,
) -> None:
    """
    Checks that the user is authenticated and that the required fields are present in the payload.

    Args:
        ctx_getter: Function to get the current context
        payload: The request payload to check
        required_fields: List of required field names

    Raises:
        ForbiddenError: If the user is not authenticated
        PayloadError: If any required fields are missing
    """

    ctx = ctx_getter()

    if owner_id is not None:
        if 'warden' not in ctx.roles and ctx.user_id != owner_id:
            raise ForbiddenError()

    if not ctx.authenticated:
        raise ForbiddenError()

    if required_fields is None:
        required_fields = []

    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise PayloadError(missing_fields)
