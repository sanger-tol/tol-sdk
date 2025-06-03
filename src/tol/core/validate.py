# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .data_object import DataObject, ErrorObject


class ValidationSeverity(str, Enum):
    ERROR = 'error'
    WARNING = 'warning'


@dataclass(frozen=True, kw_only=True)
class ValidationResult:
    object_id: str
    """Maps to the row number from the original spreadsheet"""

    detail: str
    """A helpful error message"""

    severity: ValidationSeverity
    """Either `'warning'` or `'error'`"""

    field: str | list[str] | None = None
    """
    The field(s) that failed validation

    `None` indicates the all fields failed on this row
    """

    code: str | None = None
    """An (optional) reference to an external error code"""


class Validator(ABC):
    """
    Validates a stream of `DataObject` instances.

    Note - a `Validator` child does not alter
    said stream.
    """

    def __init__(self) -> None:
        super().__init__()

        self.__results: list[ValidationResult] = []

    @abstractmethod
    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        """Validates a single `DataObject` instance."""

    def validate(
        self,
        object_stream: Iterable[DataObject | ErrorObject]
    ) -> Iterable[DataObject | ErrorObject]:
        """
        Validates a stream of `DataObject` instances.
        """

        for obj in object_stream:
            if isinstance(obj, DataObject):
                self._validate_data_object(obj)

            yield obj

    def add_warning(
        self,
        *,
        object_id: str,
        detail: str,
        field: str | list[str] | None = None,
        code: str | None = None,
    ) -> None:

        self._add_result(
            object_id=object_id,
            detail=detail,
            severity=ValidationSeverity.WARNING,
            field=field,
            code=code,
        )

    def add_error(
        self,
        *,
        object_id: str,
        detail: str,
        field: str | list[str] | None = None,
        code: str | None = None,
    ) -> None:

        self._add_result(
            object_id=object_id,
            detail=detail,
            severity=ValidationSeverity.ERROR,
            field=field,
            code=code,
        )

    @property
    def results(self) -> list[ValidationResult]:
        return self.__results

    @property
    def warnings(self) -> list[ValidationResult]:
        return list(
            self.__get_results_by_severity(
                ValidationSeverity.WARNING
            )
        )

    @property
    def errors(self) -> list[ValidationResult]:
        return list(
            self.__get_results_by_severity(
                ValidationSeverity.ERROR
            )
        )

    @property
    def has_no_errors(self) -> bool:
        """
        Returns `True` if there are no validation errors.
        """

        error_results = self.__get_results_by_severity(
            ValidationSeverity.ERROR,
        )

        return not any(error_results)

    def _add_result(
        self,
        *,
        object_id: str,
        detail: str,
        severity: ValidationSeverity,
        field: str | list[str] | None = None,
        code: str | None = None,
    ) -> None:

        result = ValidationResult(
            object_id=object_id,
            detail=detail,
            severity=severity,
            field=field,
            code=code,
        )

        self.__results.append(result)

    def __get_results_by_severity(
        self,
        severity: ValidationSeverity
    ) -> Iterable[ValidationResult]:

        return (
            r
            for r in self.__results
            if r.severity == severity
        )
