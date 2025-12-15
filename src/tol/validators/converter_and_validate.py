# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from dataclasses import dataclass

from tol.core import DataObject
from tol.core.factory import DataObjectFactory
from tol.core.validate import ValidationResult, Validator


class ConverterAndValidateValidator(Validator):
    """
    Convert DataObjects, validate the converted ones, and return the original
    input unchanged. Inner validator results are not merged here.

    {
        "converters": [{
            "module": "<path.to.module>",
            "class_name": "<path.to.ConverterClass>",
            "config_details": { ... }
        }],
        "validators": [{
            "module": "<path.to.module>",
            "class_name": "<path.to.ValidatorClass>",
            "config_details": { ... }
        }]
    }

    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        converters: list[dict]
        validators: list[dict]

    __slots__ = [
        '__converters',
        '__validators'
    ]

    def __init__(
        self,
        config: Config,
        data_object_factory: DataObjectFactory,
        **kwargs
    ) -> None:
        super().__init__()
        self.__converters = []
        self.__validators = []

        for conv in config.converters:
            __module = importlib.import_module(conv.get('module'))
            converter_class = getattr(__module, conv.get('class_name'))

            converter_conf = converter_class.Config(
                **conv.get('config_details')
            )
            self.__converters.append(converter_class(
                data_object_factory=data_object_factory,
                config=converter_conf,
            ))
        for val in config.validators:
            __module = importlib.import_module(val.get('module'))
            validator_class = getattr(__module, val.get('class_name'))

            validator_conf = validator_class.Config(
                **val.get('config_details')
            )
            self.__validators.append(validator_class(
                data_object_factory=data_object_factory,
                config=validator_conf,
            ))

    def _validate_data_object(self, obj: DataObject) -> None:
        converted_objs = [obj]
        for converter in self.__converters:
            converted_objs = converter.convert_iterable(converted_objs)
        for obj in converted_objs:
            for validator in self.__validators:
                validator._validate_data_object(obj)

    @property
    def results(self) -> list[ValidationResult]:
        return [result for validator in self.__validators for result in validator.results]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [warning for validator in self.__validators for warning in validator.warnings]

    @property
    def errors(self) -> list[ValidationResult]:
        return [error for validator in self.__validators for error in validator.errors]
