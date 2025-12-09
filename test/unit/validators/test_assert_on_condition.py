# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import AssertOnConditionValidator, Condition


class TestAssertOnConditionValidator:
    def test_no_results(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        config = AssertOnConditionValidator.Config(
            condition={
                'field': 'key1',
                'operator': '==',
                'value': 'b',
            },
            assertions=[
                {
                    'field': 'key2',
                    'operator': '==',
                    'value': 'b',
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                },
            ],
        )

        validator = AssertOnConditionValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # There should be no warnings or errors
        assert not validator.results

    def test_warnings(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        config = AssertOnConditionValidator.Config(
            condition={
                'field': 'key1',
                'operator': '!=',
                'value': None,
            },
            assertions=[
                {
                    'field': 'key2',
                    'operator': '==',
                    'value': 'b',
                    'is_error': False,
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                },
            ],
        )

        validator = AssertOnConditionValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # Should be 2 warnings, from data objects 1 and 3, from key2
        assert validator.has_no_errors
        assert len(validator.results) == 2

    def test_errors(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        config = AssertOnConditionValidator.Config(
            condition={
                'field': 'key1',
                'operator': '!=',
                'value': None,
            },
            assertions=[
                {
                    'field': 'key2',
                    'operator': '==',
                    'value': 'b',
                    'is_error': True,
                },
                {
                    'field': 'key3',
                    'operator': '!=',
                    'value': None,
                },
            ],
        )

        validator = AssertOnConditionValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        # Should be 2 errors, from data objects 1 and 3, from key2
        assert not validator.warnings
        assert len(validator.errors) == 2
