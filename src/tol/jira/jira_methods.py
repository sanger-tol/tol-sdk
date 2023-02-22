# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# Methods for reading from JIRA object.

from ..api_base.utils import parse_filters


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
    species_id = str(issue.fields.summary)

    if species_id != '':
        species_id = species_id.replace(' GenomeArk assembly', '')
        species_id = species_id.replace(' ERGA assembly', '')
        species_id = species_id.replace(' Darwin assembly', '')
        species_id = species_id.replace(' faculty assembly', '')
        species_id = species_id.replace(' ASG assembly', '')
        species_id = species_id.replace(' VGP assembly', '')
        species_id = species_id.replace(' external assembly', '')
        species_id = species_id.replace(' assembly', '')

        return species_id
    else:
        return ''


# Methods to build up Jira Query Language string.

def add_contains_str_filter(jql_field_map, filter_dict, field_key):
    field_value = filter_dict.get(field_key, '')
    if jql_field_map[field_key][1] == 'contains':
        return f" AND {jql_field_map[field_key][0]} ~ '*{field_value}*'" if field_value else ''
    elif jql_field_map[field_key][1] == 'equals':
        return f" AND {jql_field_map[field_key][0]} = '{field_value}'" if field_value else ''
    else:
        return ''


def parse_filter_str_to_dict(filter_str):
    (exact_filters, _) = parse_filters(filter_str)

    return (
        exact_filters
        if exact_filters is not None
        else {}
    )


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
        jql += f' ORDER BY {jql_field_map[sort_field][0]} {sort_direction}' \
            if sort_field or jql_field_map[sort_field][0] else ''

    return jql
