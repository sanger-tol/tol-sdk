# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .data_object import DataObject, ErrorObject


class ValidationSeverity(Enum, str):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, kw_only=True)
class ValidationResult:
    severity: ValidationSeverity
    """Either `'warning'` or `'error'`"""

    detail: str
    """A helpful error message"""

    object_id: str
    """Maps to the row number from the original spreadsheet"""

    field: str | list[str] | None = None
    """
    The field(s) that failed validation

    `None` indicates the all fields failed on this row
    """

    code: str | None = None
    """An (optional) reference to an external error code"""


class Validator(ABC):

    def __init__(self) -> None:
        super().__init__()

        self.__results: list[ValidationResult] = []

    @abstractmethod
    def _validate_object(
        self,
        obj: DataObject
    ) -> DataObject:
        """Validates a `DataObject` instance."""

    def validate(
        self,
        object_stream: Iterable[DataObject | ErrorObject]
    ) -> Iterable[DataObject | ErrorObject]:
        """
        Validates a stream of `DataObject` instances.
        """

        for obj in object_stream:
            if isinstance(obj, ErrorObject):
                yield obj
            else:
                yield self._validate_object(obj)

    def add_validation_result(
        self,
        result: ValidationResult,
    ) -> None:

        self.__results.append(result)

    def get_validation_results(
        self,
    ) -> list[ValidationResult]:

        return self.__results

    @property
    def no_errors(self) -> bool:
        """
        Returns `True` if there are no validation errors.
        """

        return not any(
            r.severity == ValidationSeverity.ERROR
            for r in self.__results
        )
