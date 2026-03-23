# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from pathlib import Path
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject
from tol.validators import JsonSchemaValidator


def _write_schema(tmp_path: Path, draft: str = '2020-12') -> Path:
    schema = {
        '$schema': f'https://json-schema.org/draft/{draft}/schema',
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'},
        },
        'required': ['name', 'age'],
        'additionalProperties': False,
    }
    schema_path = tmp_path / 'schema.json'
    schema_path.write_text(json.dumps(schema))
    return schema_path


def _make_obj(object_id: str, jsondata) -> DataObject:
    obj = create_autospec(DataObject)
    obj.id = object_id
    obj.jsondata = jsondata
    return obj


class TestJsonSchemaValidator:

    def test_valid_data(self, tmp_path: Path) -> None:
        validator = JsonSchemaValidator(
            JsonSchemaValidator.Config(schema_path=_write_schema(tmp_path))
        )
        list(validator.validate([_make_obj('a', {'name': 'Alice', 'age': 30})]))
        assert not validator.results

    def test_invalid_data(self, tmp_path: Path) -> None:
        validator = JsonSchemaValidator(
            JsonSchemaValidator.Config(schema_path=_write_schema(tmp_path))
        )
        list(validator.validate([_make_obj('a', {'name': 'Alice', 'age': 'wrong'})]))
        assert not validator.warnings
        assert len(validator.errors) == 1

    def test_missing_field(self, tmp_path: Path) -> None:
        validator = JsonSchemaValidator(
            JsonSchemaValidator.Config(schema_path=_write_schema(tmp_path))
        )
        obj = create_autospec(DataObject)
        obj.id = 'a'
        obj.jsondata = None
        list(validator.validate([obj]))
        assert not validator.warnings
        assert len(validator.errors) == 1

    def test_wrong_draft_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match='Schema draft version mismatch'):
            JsonSchemaValidator(
                JsonSchemaValidator.Config(schema_path=_write_schema(tmp_path, draft='2019-09'))
            )

    def test_warnings_when_is_error_false(self, tmp_path: Path) -> None:
        validator = JsonSchemaValidator(
            JsonSchemaValidator.Config(
                schema_path=_write_schema(tmp_path),
                is_error=False,
            )
        )
        list(validator.validate([_make_obj('a', {'name': 'Alice', 'age': 'wrong'})]))
        assert validator.has_no_errors
        assert len(validator.results) == 1
