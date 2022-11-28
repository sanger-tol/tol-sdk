# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .sanitise import sanitise_value


def flatten_entity(entity):
    flattened_entity = {}
    for field, value in entity.items():
        if type(value) is list:
            for index, subentity in enumerate(value):
                for subfield, subvalue in subentity.items():
                    new_name = field + '_' + str(index) + '_' + subfield
                    flattened_entity[new_name] = subvalue
        elif type(value) is dict:
            for subfield, subvalue in value.items():
                new_name = field + '_' + subfield
                flattened_entity[new_name] = subvalue
        else:
            flattened_entity[field] = value
    return flattened_entity


def convert_sts_entity_to_eln_entity_fields(sts_entity, mapping):
    eln_entity = {}
    flattened_entity = flatten_entity(sts_entity)
    for sts_name, eln_name in mapping['field_mappings'].items():
        if sts_name in flattened_entity:
            eln_entity[eln_name] = sanitise_value(flattened_entity[sts_name])
    return eln_entity
