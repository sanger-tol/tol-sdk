# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
import itertools
from dataclasses import dataclass, field
from typing import Iterable

from tol.core import DataObject
from tol.core.data_object_converter import DataObjectToDataObjectOrUpdateConverter
from tol.core.factory import DataObjectFactory
from tol.core.validate import ValidationResult, Validator


class ConvertorAndValidateValidator(Validator):
    """
    Convert DataObjects, validate the converted ones, and return the original
    input unchanged. Inner validator results are not merged here.

    {
        "converters": [{
            "module": "<path.to.module>",
            "class_name": "<path.to.ConverterClass>",
            "config": { ... }
        }],
        "validators": [{
            "module": "<path.to.module>",
            "class_name": "<path.to.ValidatorClass>",
            "config": { ... }
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
    converters = []
    validators = []

    def __init__(
        self,
        config: Config,
        data_object_factory: DataObjectFactory,
        **kwargs
    ) -> None:
        super().__init__()

        for conv in config.converters:
            __module = importlib.import_module(conv.get('module'))
            converter_class = getattr(__module, conv.get('class_name'))

            converter_conf = converter_class.Config(
                **conv.config
            )
            self.__converters.append(converter_class(
                data_object_factory=data_object_factory,
                config=converter_conf,
            ))
        for val in config.validators:
            __module = importlib.import_module(val.get('module'))
            validator_class = getattr(__module, val.get('class_name'))

            validator_conf = validator_class.Config(
                **val.config
            )
            self.__validators.append(validator_class(
                data_object_factory=data_object_factory,
                config=validator_conf,
            ))

    def _validate_data_object(self, obj: DataObject) -> None:
        converted_iterable = itertools.chain(
            converter.convert(obj) for converter in self.__converters
        )
        for obj in converted_iterable:
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
