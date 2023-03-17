# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

from tol.api_base import IdSchemes, Methods, Sources, tol_fields
from tol.api_base.utils.config import IndividualConfig


INDIVIDUAL_CONFIG_DICT = {
    'object_type': 'specimen',
    'meta': {},
    'source': Sources.DATABASE,
    'id_scheme': IdSchemes.EXTERNAL,
    'methods': {
        'auth': [
            Methods.GET_LIST_PAGE
        ],
        'noauth': [
            Methods.GET_BY_ID
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
        'many': [
            'samples'
        ]
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
