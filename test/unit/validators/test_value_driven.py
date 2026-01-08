# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import sys
from unittest.mock import MagicMock, create_autospec

from tol.core import DataObject
from tol.validators import ValueDrivenValidator


class TestValueDrivenValidator:
    def test_validator_cached(self):
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

        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(sys.modules['validators.unique_value_check'], 'UniqueValueCheckValidator', DummyValidator)

        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'value_one'

        config = ValueDrivenValidator.Config(
            key_column='key_column',
            validations={
                'value_one': {
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(config)
        list(validator.validate(iter([mock_one, mock_two])))
        cached = validator._ValueDrivenValidator__cached_validators
        assert len(cached) == 1
        instance = cached['value_one']
        assert instance.called == ['a', 'b']

    def test_multiple_validators(self):
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

        sys.modules['validators.unique_value_check'] = MagicMock()
        sys.modules['validators.other_value_check'] = MagicMock()
        setattr(sys.modules['validators.unique_value_check'], 'UniqueValueCheckValidator', DummyValidator)
        setattr(sys.modules['validators.other_value_check'], 'OtherValueCheckValidator', DummyValidator)

        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'value_two'

        config = ValueDrivenValidator.Config(
            key_column='key_column',
            validations={
                'value_one': {
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    }
                },
                'value_two': {
                    'module': 'validators.other_value_check',
                    'class_name': 'OtherValueCheckValidator',
                    'config_details': {
                        'field': 'c',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(config)
        list(validator.validate(iter([mock_one, mock_two])))
        cached = validator._ValueDrivenValidator__cached_validators
        assert len(cached) == 2
        assert cached['value_one'].called == ['a']
        assert cached['value_two'].called == ['b']

    def test_failing_validator(self):
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

        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(sys.modules['validators.unique_value_check'], 'UniqueValueCheckValidator', DummyValidator)

        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'

        config = ValueDrivenValidator.Config(
            key_column='key_column',
            validations={
                'value_one': {
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(config)
        try:
            list(validator.validate(iter([mock_one])))
            assert False, 'Should have raised Exception'
        except Exception as e:
            assert str(e) == 'Subvalidator failed'

    def test_invalid_config(self):
        """
        Tests that an invalid config raises the correct exception
        """
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'value_one'

        config = ValueDrivenValidator.Config(
            key_column='key_column',
            validations={
                'value_one': {
                    # keys are missing here
                    'config_details': {
                        'field': 'b',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(config)
        threw_exception = False
        try:
            list(validator.validate(iter([mock_one, mock_two])))
        except Exception as e:
            threw_exception = True
            assert e.args[0] == 'ValueDrivenValidator set up incorrectly. Failed to retrieve validator information from config'
        assert threw_exception

    def test_valid(self):
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

        sys.modules['validators.unique_value_check'] = MagicMock()
        setattr(sys.modules['validators.unique_value_check'], 'UniqueValueCheckValidator', DummyValidator)

        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'value_one'

        config = ValueDrivenValidator.Config(
            key_column='key_column',
            validations={
                'value_one': {
                    'module': 'validators.unique_value_check',
                    'class_name': 'UniqueValueCheckValidator',
                    'config_details': {
                        'field': 'b',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(config)
        list(validator.validate(iter([mock_one])))
        cached = validator._ValueDrivenValidator__cached_validators
        assert cached['value_one'].called == ['a']
