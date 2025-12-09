# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject
from tol.core.data_object_converter import DataObjectToDataObjectOrUpdateConverter
from tol.core.validate import ValidationSeverity, Validator, ValidationResult
from tol.core.factory import DataObjectFactory
from tol.validators.convertor_and_validate import ConvertorAndValidateValidator


class TestConvertorAndValidateValidator:

    def test_no_inner_results(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:

        class NoOpConverter(
            DataObjectToDataObjectOrUpdateConverter
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, data_object_factory, config: Config):
                # No-op; just satisfy expected signature
                self._config = config

            def convert(
                self,
                input_: Iterable[DataObject]
            ) -> Iterable[DataObject]:
                return tuple(input_)

        class NoOpValidator(
            Validator
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, config: Config):
                super().__init__()
                self._config = config

            def _validate_data_object(
                self,
                obj: DataObject
            ) -> None:
                pass

        config = ConvertorAndValidateValidator.Config(
            converter_class=NoOpConverter,
            validator_class=NoOpValidator,
        )

        class DummyFactory:
            pass

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=DummyFactory(),
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.results

    def test_warnings(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:

        class PassThroughConverter(
            DataObjectToDataObjectOrUpdateConverter
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, data_object_factory, config: Config):
                self._config = config

            def convert(
                self,
                input_: Iterable[DataObject]
            ) -> Iterable[DataObject]:
                return tuple(input_)

        class WarningValidator(
            Validator
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, config: Config):
                self._config = config
                self._results: list[ValidationResult] = []

            def _validate_data_object(
                self,
                obj: DataObject
            ) -> None:
                self._results.append(
                    ValidationResult(
                        object_id=obj.id,
                        detail="dummy warning",
                        severity=ValidationSeverity.WARNING,
                        field="key1",
                        code="DUMMY_WARN",
                    )
                )

            def validate(self, objs: Iterable[DataObject]) -> None:
                for o in objs:
                    self._validate_data_object(o)

            @property
            def results(self) -> list[ValidationResult]:
                return list(self._results)

            def get_results_by_severity(self, severity: ValidationSeverity) -> Iterable[ValidationResult]:
                return [r for r in self._results if r.severity == severity]

        config = ConvertorAndValidateValidator.Config(
            converter_class=PassThroughConverter,
            validator_class=WarningValidator,
        )

        class DummyFactory:
            pass

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=DummyFactory(),
        )

        # consume the Iterable
        list(validator.validate(mock_objs))

        assert validator.has_no_errors
        assert len(validator.results) == len(list(mock_objs))

    def test_errors(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:

        class PassThroughConverter(
            DataObjectToDataObjectOrUpdateConverter
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, data_object_factory, config: Config):
                self._config = config

            def convert(
                self,
                input_: Iterable[DataObject]
            ) -> Iterable[DataObject]:
                return tuple(input_)

        class ErrorValidator(
            Validator
        ):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            def __init__(self, config: Config):
                self._config = config
                self._results: list[ValidationResult] = []

            def _validate_data_object(
                self,
                obj: DataObject
            ) -> None:
                self._results.append(
                    ValidationResult(
                        object_id=obj.id,
                        detail="dummy error",
                        severity=ValidationSeverity.ERROR,
                        field="key1",
                        code="DUMMY_ERR",
                    )
                )

            def validate(self, objs: Iterable[DataObject]) -> None:
                for o in objs:
                    self._validate_data_object(o)

            @property
            def results(self) -> list[ValidationResult]:
                return list(self._results)

            def get_results_by_severity(self, severity: ValidationSeverity) -> Iterable[ValidationResult]:
                return [r for r in self._results if r.severity == severity]

        config = ConvertorAndValidateValidator.Config(
            converter_class=PassThroughConverter,
            validator_class=ErrorValidator,
        )

        class DummyFactory:
            pass

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=DummyFactory(),
        )

        # consume the Iterable
        list(validator.validate(mock_objs))

        assert not validator.warnings
        assert len(validator.errors) == len(list(mock_objs))
