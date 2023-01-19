# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# Methods for reading from JIRA object.

def get_species_name(issue):
    species_name = issue.fields.customfield_11676

    if species_name:

        # Trim unused common name
        suffix = ' ()'
        if species_name.endswith(suffix):
            species_name = species_name[:-len(suffix)]

        return species_name
    else:
        return ''


def get_species_id(issue):
    species_id = issue.fields.customfield_11627

    if species_id:
        return species_id
    else:
        return ''


# Methods to build up Jira Query Language string.

def add_contains_str_filter(jql_field_map, filter_dict, field_key):
    field_value = filter_dict.get(field_key, '')
    return f" AND {jql_field_map[field_key]} ~ '*{field_value}*'" if field_value else ''


def parse_filter_str_to_dict(filter_str):
    filter_dict = {}

    # Trim '[' and ']'
    if filter_str:
        filter_str = filter_str[1:-1]

        for filter_val in filter_str.split(','):
            filter_tuple = filter_val.split('==')

            if len(filter_tuple) >= 2:
                filter_dict[filter_tuple[0]] = filter_tuple[1]

    return filter_dict


def apply_filter_sort_to_jql(jql, jql_field_map, filter_, sort_by):
    # As JIRA field names do not match those within application,
    # fields need mapping then adding to jql.

    # Convert filter string to dictionary
    filter_dict = parse_filter_str_to_dict(filter_)

    # Add filters to fields, if filter set.
    jql += ''.join([add_contains_str_filter(jql_field_map, filter_dict, key)
                   for key in jql_field_map])

    # Add sort to JQL
    if sort_by:
        (sort_field, sort_direction) = (sort_by[1:], 'DESC') if sort_by[0] == '-' \
            else (sort_by, 'ASC')
        jql += f' ORDER BY {jql_field_map[sort_field]} {sort_direction}' \
            if sort_field or jql_field_map[sort_field] else ''

    return jql
