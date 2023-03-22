# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

from tol.api_base import tol_fields
from tol.api_base.utils.config import IndividualConfig

from .data_source import _TestDataSource


INDIVIDUAL_CONFIG_DICT = {
    'object_type': 'specimen',
    'meta': {},
    'data_source': _TestDataSource({}),
    'id_field': tol_fields.Id(),
    'methods': {
        'auth': [
            'get_list_page'
        ],
        'noauth': [
            'get_by_id'
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


class TestNoFields:
    def test_no_meta(self):
        config_copy = deepcopy(INDIVIDUAL_CONFIG_DICT)
        del config_copy['meta']
        IndividualConfig(**config_copy)

    def test_no_attributes(self):
        config_copy = deepcopy(INDIVIDUAL_CONFIG_DICT)
        del config_copy['attributes']
        IndividualConfig(**config_copy)

    def test_no_relationships(self):
        config_copy = deepcopy(INDIVIDUAL_CONFIG_DICT)
        del config_copy['relationships']
        IndividualConfig(**config_copy)
