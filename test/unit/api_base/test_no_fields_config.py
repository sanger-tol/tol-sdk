# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

from tol.api_base import tol_fields, IdSchemes, Methods, Sources
from tol.api_base.utils.config import IndividualConfig


INDIVIDUAL_CONFIG_DICT = {
    'type_': 'specimen',
    'meta': {},
    'source': Sources.DATABASE,
    'id_scheme': IdSchemes.EXTERNAL,
    'methods': {
        'auth': [
            Methods.CREATE, Methods.DELETE, Methods.UPDATE, Methods.UPSERT
        ],
        'noauth': [
            Methods.GET, Methods.BULK_GET
        ]
    },
    'attributes': {
        'tolid': tol_fields.String(unique=True, example='mHomSap52', required=True),
        'active': tol_fields.Boolean(required=False)
    },
    'relationships': {
        'one': {
            'species': {
                'key': 'taxon_id',
                'field': tol_fields.ForeignKey(required=True, example='9606'),
                'target_type': 'species'
            },
            'creator': {
                'key': 'created_by',
                'field': tol_fields.ForeignKey(
                    required=True,
                    example='1',
                    dump_only=True
                ),
                'target_type': 'users'
            }
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
