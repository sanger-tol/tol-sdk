# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from dataclasses import dataclass
from typing import Any, Dict, List

from tol.core import DataObject
from tol.core.validate import ValidationResult, Validator


class ValueDrivenValidator(Validator):
    """
    Runs different validators depending on the value of a specific column.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        """
        ```
        key_column='column_name',
        validations={
            'value_one': {
                "module": "<path.to.module>",
                "class_name": "<path.to.ValidatorClass>",
                "config_details": { ... }
            },
            'value_two': {
                "module": "<path.to.module>",
                "class_name": "<path.to.ValidatorClass>",
                "config_details": { ... }
            }
        }
        ```
        """
        key_column: str
        validations: Dict[Any, Dict[Any, Any]]

    __slots__ = ['__config', '__cached_validators']
    __config: Config
    __cached_validators: Dict[Any, Validator]

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:
        super().__init__()

        del kwargs
        self.__config = config
        self.__cached_validators = {}

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        value = obj.get_field_by_name(self.__config.key_column)
        if value in self.__cached_validators:
            # Use existing validator
            validator = self.__cached_validators[value]
            validator._validate_data_object(obj)
        else:
            # Create new validator
            try:
                validator_metaconfig = self.__config.validations[value]
                validator_module = importlib.import_module(validator_metaconfig['module'])
                validator_class = getattr(validator_module, validator_metaconfig['class_name'])
                validator_config = validator_class.Config(
                    **validator_metaconfig['config_details']
                )
            except KeyError:
                raise Exception(
                    'ValueDrivenValidator set up incorrectly. '
                    'Failed to retrieve validator information from config'
                )
            validator = validator_class(
                config=validator_config,
            )
            validator._validate_data_object(obj)

            # Add the new validator to cached validators
            self.__cached_validators[value] = validator

    @property
    def results(self) -> List[ValidationResult]:
        """
        Get results from all sub-validators, collated into a single list
        """
        return [
            result
            for validator in self.__cached_validators.values()
            for result in validator.results
        ]

    @property
    def warnings(self) -> List[ValidationResult]:
        """
        Get warnings from all sub-validators, collated into a single list
        """
        return [
            warning
            for validator in self.__cached_validators.values()
            for warning in validator.warnings
        ]

    @property
    def errors(self) -> List[ValidationResult]:
        """
        Get errors from all sub-validators, collated into a single list
        """
        return [
            error
            for validator in self.__cached_validators.values()
            for error in validator.errors
        ]
