# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

from marshmallow_jsonapi import fields as schema_fields

from tol.api_base import tol_fields
from tol.api_base.schema.auto import AutoSchemaGenerator
from tol.api_base.utils.config import IndividualConfig

from .data_source import _TestDataSource

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
    'object_type': 'specimen',
    'data_source': _TestDataSource({}),
    'id_field': tol_fields.Id(),
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

    def test_dump_only(self):
        copy_dict = deepcopy(INDIVIDUAL_CONFIG_DICT)
        copy_dict['id_field'] = tol_fields.Id(dump_only=True)
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**copy_dict)
        )
        schema_class = generator.generate()
        id_field = schema_class._declared_fields['id']

        assert id_field.dump_only is True

    def test_renamed_many_relationship(self):
        # rename the "samples" many-relationship
        copy_dict = deepcopy(INDIVIDUAL_CONFIG_DICT)
        copy_dict['relationships']['many'] = {
            'test_samples': 'samples'
        }
        # generate the auto schema
        generator = AutoSchemaGenerator(
            IndividualConfig(**copy_dict)
        )
        schema_class = generator.generate()
        fields = schema_class._declared_fields
        assert 'test_samples' in fields
        assert 'samples' not in fields
        # assert that test_samples points to samples
        assert fields['test_samples'].type_ == 'samples'
