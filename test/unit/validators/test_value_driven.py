# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import ValueDrivenValidator


class TestValueCheckValidator:
    # def test_validator_cached(
    #     self,
    #     mock_objs: Iterable[DataObject]
    # ) -> None:
    #     """
    #     Uses two data objects that have the same value for their key column. Tests whether the
    #     validator used for the second data object is the same as the one used for the first.
    #     """
    #     # Discard the sample mock objects (which won't be useful for this test)
    #     mock_one: DataObject = create_autospec(DataObject)
    #     mock_one.id = 'a'
    #     mock_one.attributes = {
    #         'key_column': 'value_one',
    #         'b': 'b',
    #     }
    #     mock_one.key_column = 'value_one'
    #     mock_one.b = 'b'
    #     mock_two: DataObject = create_autospec(DataObject)
    #     mock_two.id = 'b'
    #     mock_two.attributes = {
    #         'key_column': 'value_one',
    #         'b': 'b',
    #     }
    #     mock_two.key_column = 'value_one'
    #     mock_two.b = 'b'

    #     config = ValueDrivenValidator.Config(
    #         key_column='value_one',
    #         validations={
    #             'value_one': {
    #                 'module': 'validators.unique_value_check',
    #                 'class_name': 'UniqueValueCheckValidator',
    #                 'config_details': {
    #                     'field': 'b',
    #                 }
    #             }
    #         }
    #     )

    #     validator = ValueDrivenValidator(config)

    #     # consume the `Iterable`
    #     list(
    #         validator.validate(iter([mock_one, mock_two]))
    #     )
    #     assert validator.results

    # def test_multiple_validators(
    #     self,
    #     mock_objs: Iterable[DataObject]
    # ) -> None:
    #     """
    #     Tests whether the validator is able to work with multiple validators at once
    #     """
    #     pass

    # def test_failing_validator(
    #     self,
    #     mock_objs: Iterable[DataObject]
    # ) -> None:
    #     """
    #     Tests whether the overall validator fails as expected if one of its subvalidators fails
    #     """
    #     pass

    def test_invalid_config(
        self,
        # mocks_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'key_column': 'value_one',
            'b': 'b',
        }
        mock_one.key_column = 'value_one'
        mock_one.b = 'b'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'key_column': 'value_one',
            'b': 'b',
        }
        mock_two.key_column = 'value_one'
        mock_two.b = 'b'

        config = ValueDrivenValidator.Config(
            key_column='value_one',
            validations={
                'value_one': {
                    # keys are missing here
                    'config_details': {
                        'field': 'b',
                    }
                }
            }
        )

        validator = ValueDrivenValidator(
            config=config
        )

        threw_exception = False
        try:
            # consume the `Iterable`
            list(
                validator.validate(iter([mock_one, mock_two]))
            )
        except Exception as e:
            threw_exception = True
            assert e.args[0] == 'ValueDrivenValidator set up incorrectly. ' + \
                'Failed to retrieve validator information from config'

        assert threw_exception

    # def test_valid(
    #     self,
    #     mock_objs: Iterable[DataObject],
    # ) -> None:
    #     # Discard the sample mock objects (which won't be useful for this test)
    #     mock_one: DataObject = create_autospec(DataObject)
    #     mock_one.id = 'a'
    #     mock_one.attributes = {
    #         'SYMBIONT': 'SYMBIONT',
    #     }
    #     mock_one.SYMBIONT = 'SYMBIONT'

    #     config = ValueCheckValidator.Config(
    #         field='SYMBIONT',
    #         value='SYMBIONT'
    #     )

    #     validator = ValueCheckValidator(config)

    #     # consume the `Iterable`
    #     list(
    #         validator.validate(iter([mock_one]))
    #     )
    #     assert validator.results
