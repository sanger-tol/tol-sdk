# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import copy
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators.json_schema_definition import JsonSchemaDefinitionValidator


SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema#',
    'type': 'object',
    'properties': {
        'metadata': {
            'type': 'object',
            'properties': {
                'doi': {'type': 'string'},
                'title': {'type': 'string'},
            },
            'required': ['doi', 'title']
        },
        'software_tools': {'type': 'array'},
        'references': {'type': 'array'},
        'methods': {'type': 'object'},
        'assembly_stats': {
            'type': 'object',
            'properties': {
                'species': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'ncbi_taxonomy_id': {'type': 'string', 'minLength': 1},
                        },
                        'required': ['ncbi_taxonomy_id']
                    }
                }
            }
        },
        'reviewer_reports': {'type': 'array'},
        'publication_metadata': {'type': 'object'}
    },
    'required': [
        'metadata',
        'software_tools',
        'references',
        'methods',
        'assembly_stats',
        'reviewer_reports',
        'publication_metadata'
    ]
}

VALID_JSON = {
    'metadata': {
        'doi': '10.12345/test',
        'title': 'Test Genome Note'
    },
    'software_tools': [],
    'references': [],
    'methods': {},
    'assembly_stats': {
        'species': [
            {
                'ncbi_taxonomy_id': '9606',
            }
        ]
    },
    'reviewer_reports': [],
    'publication_metadata': {}
}


def _make_obj(object_id: str, data: dict) -> DataObject:
    obj = create_autospec(DataObject)
    obj.id = object_id
    obj.data = data
    return obj


class TestGenomeNoteJsonSchemaDefinitionValidator:

    def test_valid_genome_note_json(self) -> None:
        validator = JsonSchemaDefinitionValidator(
            JsonSchemaDefinitionValidator.Config(
                json_schema=SCHEMA,
            ),
        )

        list(validator.validate([
            _make_obj('test', VALID_JSON),
        ]))

        assert not validator.results

    def test_invalid_missing_required_top_level_field(self) -> None:
        data = copy.deepcopy(VALID_JSON)
        del data['metadata']

        validator = JsonSchemaDefinitionValidator(
            JsonSchemaDefinitionValidator.Config(
                json_schema=SCHEMA,
            ),
        )

        list(validator.validate([
            _make_obj('test', data),
        ]))

        assert not validator.warnings
        assert len(validator.errors) == 1
        assert "'metadata' is a required property" in validator.errors[0].detail

    def test_invalid_ncbi_taxonomy_id_type(self) -> None:
        data = copy.deepcopy(VALID_JSON)
        data['assembly_stats']['species'][0]['ncbi_taxonomy_id'] = 55149

        validator = JsonSchemaDefinitionValidator(
            JsonSchemaDefinitionValidator.Config(
                json_schema=SCHEMA,
            ),
        )

        list(validator.validate([
            _make_obj('test', data),
        ]))

        assert not validator.warnings
        assert len(validator.errors) == 1
        assert 'is not of type' in validator.errors[0].detail

    def test_missing_field(self) -> None:
        obj = create_autospec(DataObject)
        obj.id = 'test'
        obj.data = None

        validator = JsonSchemaDefinitionValidator(
            JsonSchemaDefinitionValidator.Config(
                json_schema=SCHEMA,
            ),
        )

        list(validator.validate([obj]))

        assert not validator.warnings
        assert len(validator.errors) == 1

    def test_warnings_when_is_error_false(self) -> None:
        data = copy.deepcopy(VALID_JSON)
        del data['metadata']

        validator = JsonSchemaDefinitionValidator(
            JsonSchemaDefinitionValidator.Config(
                json_schema=SCHEMA,
                is_error=False,
            ),
        )

        list(validator.validate([
            _make_obj('test', data),
        ]))

        assert validator.has_no_errors
        assert len(validator.results) == 1
