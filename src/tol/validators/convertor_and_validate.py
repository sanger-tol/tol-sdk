# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from typing import Iterable

from tol.core import DataObject
from tol.core.data_object_converter import DataObjectToDataObjectOrUpdateConverter
from tol.core.validate import ValidationSeverity, Validator, ValidationResult
from tol.core.factory import DataObjectFactory


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
        "__converter",
        "__validator",
        "__inner_errors",
        "__inner_warnings",
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

        self.__inner_errors: dict[str, list[ValidationResult]] = {}
        self.__inner_warnings: dict[str, list[ValidationResult]] = {}

    def _validate_data_object(self, obj: DataObject) -> None:
        converted_iterable: Iterable[DataObject] = self.__converter.convert((obj,))

        self.__validator.validate(converted_iterable)

        self.__record_inner_results(obj.id)
 
    @property
    def results(self) -> list[ValidationResult]:
        return self.__validator.results

    @property
    def warnings(self) -> list[ValidationResult]:
        return list(
            self.__validator.get_results_by_severity(
                ValidationSeverity.WARNING
            )
        )

    @property
    def errors(self) -> list[ValidationResult]:
        return list(
            self.__validator.get_results_by_severity(
                ValidationSeverity.ERROR
            )
        )

    @property
    def has_no_errors(self) -> bool:
        """
        Returns `True` if there are no validation errors.
        """
        error_results = self.__validator.get_results_by_severity(
            ValidationSeverity.ERROR
        )
        return len(list(error_results)) == 0

    def __record_inner_results(self, object_id: str) -> None:
        inner_results = list(self.__validator.results)

        self.__inner_errors[object_id] = [
            r for r in inner_results if r.severity == ValidationSeverity.ERROR
        ]
        self.__inner_warnings[object_id] = [
            r for r in inner_results if r.severity == ValidationSeverity.WARNING
        ]

        for r in inner_results:
            self._add_result(
                object_id=r.object_id,
                detail=r.detail,
                severity=r.severity,
                field=r.field,
                code=r.code,
            )
   
clea