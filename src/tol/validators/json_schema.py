# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from tol.core import DataObject
from tol.core.validate import Validator

EXPECTED_DRAFT = 'https://json-schema.org/draft/2020-12/schema'


class JsonSchemaValidator(Validator):
    """
    Validate JSON content of a DataObject against a Draft 2020-12 schema.
    Also enforces that the schema declares Draft 2020-12 via the $schema field.
    """

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        schema_path: Path
        field: str = 'jsondata'
        is_error: bool = True
        detail: str = 'JSON schema validation failed'

    __slots__ = ['__config', '__validator']
    __config: Config
    __validator: Draft202012Validator

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:

        del kwargs
        super().__init__()
        self.__config = config

        with open(config.schema_path) as f:
            schema = json.load(f)

        actual_draft = schema.get('$schema')
        if actual_draft != EXPECTED_DRAFT:
            raise ValueError(
                f'Schema draft version mismatch. Expected "{EXPECTED_DRAFT}", got "{actual_draft}"'
            )

        Draft202012Validator.check_schema(schema)

        self.__validator = Draft202012Validator(schema)

    def _validate_data_object(
        self,
        obj: DataObject,
    ) -> None:

        data = getattr(obj, self.__config.field, None)

        if data is None:
            self.__add_result(
                obj=obj,
                field=self.__config.field,
                detail=f'Missing field "{self.__config.field}" in DataObject'
            )
            return

        error: ValidationError = next(self.__validator.iter_errors(data), None)
        if error is not None:
            self.__add_result(
                obj=obj,
                field=self.__config.field,
                detail=f'{self.__config.detail}: {error.message}'
            )

    def __add_result(
        self,
        obj: DataObject,
        field: str,
        detail: str
    ) -> None:
        if self.__config.is_error:
            self.add_error(
                object_id=obj.id,
                detail=detail,
                field=field
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=detail,
                field=field
            )
