# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

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
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        converter_class: type[DataObjectToDataObjectOrUpdateConverter]
        converter_config: dict = field(default_factory=dict)
        validator_class: type[Validator]
        validator_config: dict = field(default_factory=dict)

    __slots__ = [
        '__converter',
        '__validator'
    ]

    def __init__(
        self,
        config: Config,
        data_object_factory: DataObjectFactory,
    ) -> None:
        super().__init__()

        converter_conf = config.converter_class.Config(
            **config.converter_config
        )
        self.__converter = config.converter_class(
            data_object_factory=data_object_factory,
            config=converter_conf,
        )
        validator_conf = config.validator_class.Config(
            **config.validator_config
        )
        self.__validator = config.validator_class(
            config=validator_conf
        )

    def _validate_data_object(self, obj: DataObject) -> None:
        converted_iterable: Iterable[DataObject] = self.__converter.convert(obj)
        for obj in converted_iterable:
            self.__validator._validate_data_object(obj)

    @property
    def results(self) -> list[ValidationResult]:
        return self.__validator.results

    @property
    def warnings(self) -> list[ValidationResult]:
        return self.__validator.warnings

    @property
    def errors(self) -> list[ValidationResult]:
        return self.__validator.errors
