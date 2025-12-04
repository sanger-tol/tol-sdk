# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import MutuallyExclusiveValidator
from tol.validators.interfaces import Condition


class TestMutuallyExclusiveValidator:
    def test_valid(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'a'
                case 'TUBE_OR_WELL_ID':
                    return 'b'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'a'
        mock_two.attributes = {
            'SYMBIONT': 'NOT SYMBIONT',
            'RACK_OR_PLATE_ID': 'c',
            'TUBE_OR_WELL_ID': 'd',
        }

        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'NOT SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'c'
                case 'TUBE_OR_WELL_ID':
                    return 'd'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two

        config = MutuallyExclusiveValidator.Config(
            first_field_where=Condition(
                field='SYMBIONT',
                operator='!=',
                value='SYMBIONT',
            ),
            second_field_where=Condition(
                field='SYMBIONT',
                operator='==',
                value='SYMBIONT',
            ),
            target_fields=[
                'RACK_OR_PLATE_ID',
                'TUBE_OR_WELL_ID',
            ],
            detail='All symbionts must have a TARGET with same rack/plate and tube/well'
        )

        validator = MutuallyExclusiveValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.results) == 0

    def test_clash_first_then_second(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'NOT SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'NOT SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'a'
                case 'TUBE_OR_WELL_ID':
                    return 'b'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'a'
        mock_two.attributes = {
            'SYMBIONT': 'SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }

        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'a'
                case 'TUBE_OR_WELL_ID':
                    return 'b'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two

        config = MutuallyExclusiveValidator.Config(
            first_field_where=Condition(
                field='SYMBIONT',
                operator='!=',
                value='SYMBIONT',
            ),
            second_field_where=Condition(
                field='SYMBIONT',
                operator='==',
                value='SYMBIONT',
            ),
            target_fields=[
                'RACK_OR_PLATE_ID',
                'TUBE_OR_WELL_ID',
            ],
            detail='All symbionts must have a TARGET with same rack/plate and tube/well'
        )

        validator = MutuallyExclusiveValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1

    def test_clash_second_then_first(
        self, mock_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SYMBIONT': 'SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'a'
                case 'TUBE_OR_WELL_ID':
                    return 'b'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'a'
        mock_two.attributes = {
            'SYMBIONT': 'NOT SYMBIONT',
            'RACK_OR_PLATE_ID': 'a',
            'TUBE_OR_WELL_ID': 'b',
        }

        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'SYMBIONT':
                    return 'NOT SYMBIONT'
                case 'RACK_OR_PLATE_ID':
                    return 'a'
                case 'TUBE_OR_WELL_ID':
                    return 'b'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two

        config = MutuallyExclusiveValidator.Config(
            first_field_where=Condition(
                field='SYMBIONT',
                operator='!=',
                value='SYMBIONT',
            ),
            second_field_where=Condition(
                field='SYMBIONT',
                operator='==',
                value='SYMBIONT',
            ),
            target_fields=[
                'RACK_OR_PLATE_ID',
                'TUBE_OR_WELL_ID',
            ],
            detail='All symbionts must have a TARGET with same rack/plate and tube/well'
        )

        validator = MutuallyExclusiveValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1
