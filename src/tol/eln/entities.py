# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .sanitise import sanitise_value


def flatten_entity(entity, level=None):
    flattened_entity = {}
    prefix = f'{level}_' if level is not None else ''
    if isinstance(entity, dict):
        for field, value in entity.items():
            extra_fields = flatten_entity(value, prefix + field)
            flattened_entity = {**flattened_entity,
                                **extra_fields}
    elif isinstance(entity, list):
        for index, subentity in enumerate(entity):
            new_name = prefix + str(index)
            extra_fields = flatten_entity(subentity, new_name)
            flattened_entity = {**flattened_entity,
                                **extra_fields}
    else:
        return {level: entity}
    return flattened_entity


def convert_sts_entity_to_eln_entity_fields(sts_entity, mapping):
    eln_entity = {}
    flattened_entity = flatten_entity(sts_entity)
    for sts_name, eln_name in mapping['field_mappings'].items():
        if sts_name in flattened_entity:
            eln_entity[eln_name] = {'value': sanitise_value(flattened_entity[sts_name], None)}
    return eln_entity
