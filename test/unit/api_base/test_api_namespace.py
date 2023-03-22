# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import tol_fields

from tol.api_base import ServiceNamespace

from .data_source import _TestDataSource


INDIVIDUAL_CONFIG_DICT = {
    'object_type': 'specimen',
    'data_source': _TestDataSource({}),
    'id': tol_fields.Id(),
    'methods': {
        'auth': [
            'get_by_id'
        ],
        'noauth': [
            'get_list_page'
        ]
    },
    'attributes': {
        'tolid': tol_fields.String(unique=True, example='mHomSap52', required=True),
        'active': tol_fields.Boolean(required=False)
    },
    'relationships': {
        'one': {
            'species': tol_fields.ToOneRelationship(
                'species',
                'taxon_id',
                required=True,
                example='9606'
            ),
            'creator': tol_fields.ToOneRelationship(
                'users',
                'created_by',
                required=True,
                example='1',
                dump_only=True
            )
        },
        'many': {
            'samples': 'samples'
        }
    }
}


class TestApiNamespace:
    pass
