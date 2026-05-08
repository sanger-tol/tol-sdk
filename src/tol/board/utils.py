# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from nanoid import generate

from ..core import DataObject

if TYPE_CHECKING:
    from ..sql import SqlDataSource


PREFIX_MAPPINGS = {
    'board': 'b',
    'view': 'v',
    'zone': 'z',
    'component': 'c',
}


def get_entity_type_from_prefix(prefix: str) -> str | None:
    """
    Returns the entity type corresponding to the given prefix.

    Args:
        prefix: A single character prefix (e.g., 'b', 'v', 'z', 'c')

    Returns:
        The entity type string (e.g., 'board', 'view', 'zone', 'component'),
        or None if the prefix is not recognized.

    Examples:
        >>> get_entity_type_from_prefix('b')
        'board'
        >>> get_entity_type_from_prefix('v')
        'view'
        >>> get_entity_type_from_prefix('x')
        None
    """
    reverse_mappings = {v: k for k, v in PREFIX_MAPPINGS.items()}
    return reverse_mappings.get(prefix)


def save_board_entity_and_children(
    board_ds: SqlDataSource,
    entities: dict[str, list[DataObject]],
    user_id: str,
    new_parent_title: str,
    parent_type: str,
    type_hierarchy: list[str],
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

    Returns:
        A tuple of (new_parent_entity_id, id_mapping) where id_mapping
        maps old IDs to newly generated IDs
    """

    custom_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    biggest_type = type_hierarchy[0]

    # Build old -> new ID mapping for all non-joiner types
    id_mapping: dict[str, str] = {}
    for entity_type, objs in entities.items():
        if entity_type in type_hierarchy:
            for obj in objs:
                new_id = f'{PREFIX_MAPPINGS.get(
                    entity_type, "x")}_{generate(custom_alphabet, 12)}'
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
                attributes={
                    **obj.attributes, 'title': new_parent_title}
                if entity_type == parent_type else obj.attributes,
                to_one=to_one,
            )
            board_ds.insert(entity_type, [new_obj])

    for entity_type, objs in entities.items():
        if entity_type not in type_hierarchy:
            bigger_t = next(t for t in type_hierarchy if entity_type.endswith(f'_{t}'))
            smaller_t = entity_type[: -(len(bigger_t) + 1)]
            for obj in objs:
                smaller_obj = getattr(obj, smaller_t)
                bigger_obj = getattr(obj, bigger_t)
                new_obj = board_ds.data_object_factory(
                    type_=entity_type,
                    attributes={'order': obj.order},
                    to_one={
                        smaller_t: board_ds.data_object_factory(
                            type_=smaller_t,
                            id_=id_mapping[smaller_obj.id],
                        ),
                        bigger_t: board_ds.data_object_factory(
                            type_=bigger_t,
                            id_=id_mapping[bigger_obj.id],
                        ),
                    },
                )
                board_ds.insert(entity_type, [new_obj])

    return id_mapping[entities[biggest_type][0].id], id_mapping
