# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from marshmallow_jsonapi import fields as schema_fields

from tol.api_base import IdSchemes, Methods, Sources, tol_fields as fields
from tol.api_base.schema.auto import AutoSchemaGenerator
from tol.api_base.utils.config import IndividualConfig

# TODO test:
# - all declared fields are on the schema
# - datatypes are correct
# - dump only is respected
# - required fields are respected
# - excluded fields are respected
# - update works correctly, with a correctly injected
#   and instantiated DataModel object
# - update is passed the ResouceMeta data


INDIVIDUAL_CONFIG = IndividualConfig(
    type_='specimen',
    meta={},
    source=Sources.DATABASE,
    id_scheme=IdSchemes.EXTERNAL,
    methods={
        'auth': [
            Methods.CREATE, Methods.DELETE, Methods.UPDATE, Methods.UPSERT
        ],
        'noauth': [
            Methods.GET, Methods.BULK_GET
        ]
    },
    attributes={
        'tolid': fields.String(unique=True, example='mHomSap52'),
        'active': fields.Boolean()
    },
    relationships={
        'one': {
            'species': {
                'key': 'taxon_id',
                'field': fields.ForeignKey(required=True, example='9606'),
                'target_type': 'species'
            },
            'creator': {
                'key': 'created_by',
                'field': fields.ForeignKey(
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
)


class TestAutoSchema:
    def test_only_correct_fields_present(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(INDIVIDUAL_CONFIG)
        schema_class = generator.generate()
        present_fields = list(schema_class._declared_fields.keys())

        # assert that all fields are present
        expected_fields = [
            'id',
            'tolid',
            'active',
            'species',
            'creator',
            'samples'
        ]
        # assert that only these fields are present
        assert present_fields == expected_fields

        # assert that relationship keys are not present
        assert 'taxon_id' not in present_fields

    def test_fields_have_correct_type(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(INDIVIDUAL_CONFIG)
        schema_class = generator.generate()
        observed_types = {
            field: type(value)
            for field, value
            in schema_class._declared_fields.items()
        }

        expected_types = {
            'id': schema_fields.String,
            'tolid': schema_fields.String,
            'active': schema_fields.Boolean,
            'species': schema_fields.Relationship,
            'creator': schema_fields.Relationship,
            'samples': schema_fields.Relationship
        }
        assert observed_types == expected_types
