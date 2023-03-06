# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

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
        'tolid': fields.String(unique=True, example='mHomSap52', required=True),
        'active': fields.Boolean(required=False)
    },
    'relationships': {
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
}


class TestAutoSchema:
    def test_only_correct_fields_present(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**INDIVIDUAL_CONFIG_DICT)
        )
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
        generator = AutoSchemaGenerator(
            IndividualConfig(**INDIVIDUAL_CONFIG_DICT)
        )
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

    def test_required_fields(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**INDIVIDUAL_CONFIG_DICT)
        )
        schema_class = generator.generate()
        observed_requireds = {
            field: value.required
            for field, value
            in schema_class._declared_fields.items()
        }

        expected_requireds = {
            'id': True,
            'tolid': True,
            'active': False,
            'species': True,
            'creator': True,
            'samples': False
        }
        assert observed_requireds == expected_requireds

    def test_dump_only_fields(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**INDIVIDUAL_CONFIG_DICT)
        )
        schema_class = generator.generate()
        observed_dump_onlys = {
            field: value.dump_only
            for field, value
            in schema_class._declared_fields.items()
        }

        expected_dump_onlys = {
            'id': False,
            'tolid': False,
            'active': False,
            'species': False,
            'creator': True,
            'samples': False
        }
        assert observed_dump_onlys == expected_dump_onlys

    def test_dump_only_true_on_auto_increment_id_scheme(self):
        # make the IdScheme auto_increment
        copy_dict = deepcopy(INDIVIDUAL_CONFIG_DICT)
        copy_dict['id_scheme'] = IdSchemes.AUTO_INCREMENT
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**copy_dict)
        )
        schema_class = generator.generate()
        id_field = schema_class._declared_fields['id']

        assert id_field.dump_only is True
