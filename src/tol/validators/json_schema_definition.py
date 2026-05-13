# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from jsonschema import Draft202012Validator

from tol.core import DataObject
from tol.core.validate import Validator


class JsonSchemaDefinitionValidator(Validator):
    """
    Validates JSON data against a JSON schema definition.
    """

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        json_schema: dict
        field: str = 'data'
        is_error: bool = True
        detail: str = 'JSON schema validation failed'

        def __post_init__(self):
            if not isinstance(self.json_schema, dict):
                raise TypeError(
                    f'json_schema must be a dict, got {type(self.json_schema).__name__}'
                )

    __slots__ = ['__config', '__validator']
    __config: Config
    __validator: Draft202012Validator

    def __init__(self, config: Config, **kwargs) -> None:
        del kwargs
        super().__init__()
        self.__config = config
        self.__validator = Draft202012Validator(config.json_schema)

    def _validate_data_object(self, obj: DataObject) -> None:
        data = getattr(obj, self.__config.field, None)
        if data is None:
            self.__add_result(
                obj=obj,
                field=self.__config.field,
                detail=f"Missing field '{self.__config.field}' in DataObject"
            )
            return
        if not isinstance(data, dict):
            self.__add_result(
                obj=obj,
                field=self.__config.field,
                detail=(
                    f'Field "{self.__config.field}" must be a dict, '
                    f'got {type(data).__name__}'
                )
            )
            return
        error = next(self.__validator.iter_errors(data), None)
        if error is not None:
            self.__add_result(
                obj=obj,
                field=self.__config.field,
                detail=(
                    f'{self.__config.detail}: {error.message}'
                )
            )

    def __add_result(self, obj: DataObject, field: str, detail: str) -> None:
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
