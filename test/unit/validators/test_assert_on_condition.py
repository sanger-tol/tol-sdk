# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import AssertOnConditionValidator


class TestAssertOnConditionValidator:
    def test_condition_false(
        self, mock_objs: Iterable[DataObject]
    ):
        config = {
            'condition': {
                'field': 'key1',
                'operator': '==',
                'value': None
            },
            'assert': [
                {
                    'field': 'key2',
                    'operator': '!=',
                    'value': None,
                    'is_error': True,
                    'message': 'key2 cannot be None' 
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                    'is_error': True,
                    'message': 'key3 cannot be None'
                }
            ]
        }
    
        validator = AssertOnConditionValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # There should be no warnings or errors
        assert not validator.results

    def test_condition_true_and_all_assertions_pass(
        self, mock_objs: Iterable[DataObject]
    ):
        config = {
            'condition': {
                'field': 'key1',
                'operator': '!=',
                'value': None
            },
            'assert': [
                {
                    'field': 'key2',
                    'operator': '!=',
                    'value': None,
                    'is_error': True,
                    'message': 'key2 cannot be None' 
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                    'is_error': True,
                    'message': 'key3 cannot be None'
                }
            ]
        }
    
        validator = AssertOnConditionValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # There should be no warnings or errors
        assert not validator.results

    def test_condition_true_and_some_assertions_fail(
        self, mock_objs: Iterable[DataObject]
    ):
        config = {
            'condition': {
                'field': 'key1',
                'operator': '!=',
                'value': None
            },
            'assert': [
                {
                    'field': 'key2',
                    'operator': '==',
                    'value': None,
                    'is_error': False,
                    'message': 'key2 cannot be None' 
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                    'is_error': False,
                    'message': 'key3 cannot be None'
                }
            ]
        }
    
        validator = AssertOnConditionValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # There should be one warning and one error (for each of the 3 data objects)
        assert len(validator.warnings) == 1 * 3
        assert len(validator.errors) == 0

    def test_condition_true_and_all_assertions_fail(
        self, mock_objs: Iterable[DataObject]
    ):
        config = {
            'condition': {
                'field': 'key1',
                'operator': '!=',
                'value': None
            },
            'assert': [
                {
                    'field': 'key2',
                    'operator': '==',
                    'value': None,
                    'is_error': True,
                    'message': 'key2 cannot be None' 
                },
                {
                    'field': 'key3',
                    'operator': '==',
                    'value': None,
                    'is_error': True,
                    'message': 'key3 cannot be None'
                }
            ]
        }
    
        validator = AssertOnConditionValidator(
            config,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # There should be no warnings and two errors (for each of the 3 data objects)
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 2 * 3
