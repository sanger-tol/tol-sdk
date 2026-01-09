# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import sys
from typing import Iterable
from unittest.mock import MagicMock, create_autospec

from tol.core import DataObject
from tol.validators import BranchingValidator


class TestBranchingValidator:
    def test_validator_cached(
        self,
        mock_objs: Iterable[DataObject]
    ):
        """
        Uses two data objects that have the same value for their key column. Tests whether the
        validator used for the second data object is the same as the one used for the first.
        """
        class DummyValidator:
            class Config:
                def __init__(self, field):
                    self.field = field

            def __init__(self, config):
                self.config = config
                self.called = []

            def _validate_data_object(self, obj):
                self.called.append(obj.id)

        # Set up a dummy validator to act as UniqueValueCheckValidator so we can keep track of
        # which data objects it validates
        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(
            sys.modules['validators.unique_value_check'],
            'UniqueValueCheckValidator',
            DummyValidator
        )

        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'value_one'

        config = BranchingValidator.Config(
            validations=[
                {
                    'condition': {
                        'field': 'key_column',
                        'operator': '==',
                        'value': 'value_one',
                    },
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    },
                },
            ]
        )

        validator = BranchingValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        # Fetch the dictionary (private attribute) of cached validators, and check that there's
        # only one (confirming that a new one was not made each time)
        cached = validator._BranchingValidator__cached_validators
        assert len(cached) == 1

        # Get this single validator, and ensure it was the same one used for both data objects
        # 'a' and 'b' by using the `called` store defined in DummyValidator
        instance = cached[0]
        assert instance.called == ['a', 'b']

    def test_multiple_validators(
        self,
        mock_objs: Iterable[DataObject]
    ):
        """
        Tests whether the validator is able to work with multiple validators at once
        """
        class DummyValidator:
            class Config:
                def __init__(self, field):
                    self.field = field

            def __init__(self, config):
                self.config = config
                self.called = []

            def _validate_data_object(self, obj):
                self.called.append(obj.id)

        # Set up dummy validators to act as UniqueValueCheckValidator so we can keep track of
        # which data objects it validates
        sys.modules['validators.unique_value_check'] = MagicMock()
        sys.modules['validators.other_value_check'] = MagicMock()
        setattr(
            sys.modules['validators.unique_value_check'],
            'UniqueValueCheckValidator',
            DummyValidator
        )
        setattr(
            sys.modules['validators.other_value_check'],
            'OtherValueCheckValidator',
            DummyValidator
        )

        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'value_two'

        config = BranchingValidator.Config(
            validations=[
                {
                    'condition': {
                        'field': 'key_column',
                        'operator': '==',
                        'value': 'value_one',
                    },
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    },
                },
                {
                    'condition': {
                        'field': 'key_column',
                        'operator': '==',
                        'value': 'value_two',
                    },
                    'module': 'validators.other_value_check',
                    'class_name': 'OtherValueCheckValidator',
                    'config_details': {
                        'field': 'c',
                    },
                },
            ]
        )

        validator = BranchingValidator(config)

        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        # Fetch the dictionary (private attribute) of cached validators, to check that each
        # sub-validation got a separate validator
        cached = validator._BranchingValidator__cached_validators
        assert len(cached) == 2

        # Ensure that the validators validated the correct data objects
        assert cached[0].called == ['a']
        assert cached[1].called == ['b']

    def test_failing_validator(
        self,
        mock_objs: Iterable[DataObject]
    ):
        """
        Tests whether the overall validator fails as expected if one of its subvalidators fails
        """
        class DummyValidator:
            class Config:
                def __init__(self, field):
                    self.field = field

            def __init__(self, config):
                self.config = config

            def _validate_data_object(self, obj):
                raise Exception('Subvalidator failed')

        # Set up a dummy validator to act as UniqueValueCheckValidator so we can keep track of
        # which data objects it validates
        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(
            sys.modules['validators.unique_value_check'],
            'UniqueValueCheckValidator',
            DummyValidator
        )

        # The provided mock objects are not appropriate for this test, so we set up a new one
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'

        config = BranchingValidator.Config(
            validations=[
                {
                    'condition': {
                        'field': 'key_column',
                        'operator': '==',
                        'value': 'value_one',
                    },
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    },
                },
            ]
        )

        validator = BranchingValidator(config)

        # Check whether the sub-validator fails (with the correct error message)
        try:
            # consume the Iterable
            list(
                validator.validate(iter([mock_one]))
            )
            assert False, 'Should have raised Exception'
        except Exception as e:
            assert str(e) == 'Subvalidator failed'

    # def test_invalid_config(
    #     self,
    #     mock_objs: Iterable[DataObject]
    # ):
    #     """
    #     Tests that an invalid config raises the correct exception
    #     """
    #     # The provided mock objects are not appropriate for this test, so we set up new ones
    #     del mock_objs
    #     mock_one: DataObject = create_autospec(DataObject)
    #     mock_one.id = 'a'
    #     mock_one.get_field_by_name.return_value = 'value_one'
    #     mock_two: DataObject = create_autospec(DataObject)
    #     mock_two.id = 'b'
    #     mock_two.get_field_by_name.return_value = 'value_one'

    #     config = BranchingValidator.Config(
    #         key_column='key_column',
    #         validations={
    #             'value_one': {
    #                 # keys are missing here
    #                 'config_details': {
    #                     'field': 'b',
    #                 }
    #             }
    #         }
    #     )

    #     validator = BranchingValidator(config)

    #     # Check whether the sub-validator fails (with the correct error message)
    #     try:
    #         # consume the Iterable
    #         list(
    #             validator.validate(iter([mock_one, mock_two]))
    #         )
    #         assert False, 'Should have raised Exception'
    #     except Exception as e:
    #         assert e.args[0] == 'BranchingValidator set up incorrectly. ' + \
    #             'Failed to retrieve validator information from config'

    def test_valid(
        self,
        mock_objs: Iterable[DataObject]
    ):
        """
        Tests a valid configuration and successful validation
        """
        class DummyValidator:
            class Config:
                def __init__(self, field):
                    self.field = field

            def __init__(self, config):
                self.config = config
                self.called = []

            def _validate_data_object(self, obj):
                self.called.append(obj.id)

        # Set up a dummy validator to act as UniqueValueCheckValidator so we can keep track of
        # which data objects it validates
        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(
            sys.modules['validators.unique_value_check'],
            'UniqueValueCheckValidator',
            DummyValidator
        )

        # The provided mock objects are not appropriate for this test, so we set up a new one
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'

        config = BranchingValidator.Config(
            validations=[
                {
                    'condition': {
                        'field': 'key_column',
                        'operator': '==',
                        'value': 'value_one',
                    },
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    },
                },
            ]
        )

        validator = BranchingValidator(config)

        # consume the Iterable
        list(
            validator.validate(iter([mock_one]))
        )

        # Ensure the expected sub-validator for this valid validation has been cached
        cached = validator._BranchingValidator__cached_validators
        assert cached[0].called == ['a']
