# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from dataclasses import dataclass
from typing import Dict, List, cast

from tol.core import DataObject
from tol.core.validate import ValidationResult, Validator

from .interfaces import Condition, ConditionDict, ConditionEvaluator


Subvalidation = Dict[str, ConditionDict | str | Dict]


class BranchingValidator(Validator, ConditionEvaluator):
    """
    This validator is configured with a list of conditions.
    If a condition passes, the corresponding sub-validator will be run.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        """
        ```
        validations=[
            {
                'condition': {
                    'field': 'column_name',
                    'operator': '==',
                    'value': 'expected_value',
                },
                'module': '<path.to.module>',
                'class_name': '<path.to.ValidatorClass>',
                'config_details': { ... },
            },
            {
                ...
            }
        ]
        ```
        """
        validations: List[Subvalidation]

    __slots__ = ['__config', '__cached_validators']
    __config: Config
    __cached_validators: Dict[int, Validator]
    """
    Stores all sub-validators that have already been seen so that they can be used again.
    Their keys are their indexes in the `validations` list in the validator config
    """

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
        for subvalidator_index, validation in enumerate(self.__config.validations):
            condition_dict = cast(ConditionDict, validation['condition'])
            if not self._does_condition_pass(Condition.from_dict(condition_dict), obj):
                continue

            if subvalidator_index in self.__cached_validators:
                # Use existing validator to perform subvalidation
                validator = self.__cached_validators[subvalidator_index]
                validator._validate_data_object(obj)
            else:
                # Create a new validator and use that for the subvalidation
                validator = self.__instantiate_validator(validation)
                validator._validate_data_object(obj)

                # Add the new validator to the store of cached validators
                self.__cached_validators[subvalidator_index] = validator

            # TODO: Should we allow multiple conditions passing?
            break

    def __instantiate_validator(self, subvalidation: Subvalidation) -> Validator:
        # Before attempting to extract items from the subvalidation, ensure all of the required
        # keys are there and that they contain values of the correct types.
        # This allows the dictionary to be safely queried thereafter
        try:
            # Accessing with square brackets will also check whether the key exists or not
            if not isinstance(subvalidation['module'], str):
                raise ValueError('module')
            elif not isinstance(subvalidation['class_name'], str):
                raise ValueError('class_name')
        except (IndexError, ValueError) as e:
            # TODO Test both of these error types work
            if isinstance(e, IndexError):
                raise Exception(
                    f'Invalid config in BranchingValidator: {e.args[0]} not found'
                )
            else:
                raise Exception(
                    f'Invalid config in BranchingValidator: '
                    f'{e.args[0]} contains erroneous value'
                )

        # Dynamically retrieve the validator class
        validator_module = importlib.import_module(subvalidation['module'])
        validator_class = getattr(validator_module, subvalidation['class_name'])
        
        # Construct and return the new validator
        validator_config = validator_class.Config(
            subvalidation['config_details']
        )
        return validator_class(
            config=validator_config,
        )

    @property
    def results(self) -> List[ValidationResult]:
        """
        Fetches results from all sub-validators, collated into a single list
        """
        return [
            result
            for validator in self.__cached_validators.values()
            for result in validator.results
        ]

    @property
    def warnings(self) -> List[ValidationResult]:
        """
        Fetches warnings from all sub-validators, collated into a single list
        """
        return [
            warning
            for validator in self.__cached_validators.values()
            for warning in validator.warnings
        ]

    @property
    def errors(self) -> List[ValidationResult]:
        """
        Fetches errors from all sub-validators, collated into a single list
        """
        return [
            error
            for validator in self.__cached_validators.values()
            for error in validator.errors
        ]
