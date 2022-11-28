# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


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
