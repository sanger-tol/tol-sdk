# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import UniqueValueCheckValidator


class TestUniqueValueCheckValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'GAL': 'SANG',
        }
        mock_one.GAL = 'SANG'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'GAL': 'EL',
        }
        mock_two.GAL = 'EL'

        config = UniqueValueCheckValidator.Config(
            field='GAL',
        )
        validator = UniqueValueCheckValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )
        assert validator.results
        assert len(validator.errors) == 1

    def test_fail(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'GAL': '',
        }
        mock_one.GAL = ''
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'GAL': 'EL',
        }
        mock_two.GAL = 'EL'
        mock_three: DataObject = create_autospec(DataObject)
        mock_three.id = 'c'
        mock_three.attributes = {
            'GAL': 'SANG',
        }
        mock_three.GAL = 'SANG'
        config = UniqueValueCheckValidator.Config(
            field='GAL',
        )
        validator = UniqueValueCheckValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two, mock_three]))
        )
        assert len(validator.errors) == 1

    def test_pass(
            self,
            mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'GAL': 'EL',
        }
        mock_one.GAL = 'EL'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'GAL': 'EL',
        }
        mock_two.GAL = 'EL'
        config = UniqueValueCheckValidator.Config(
            field='GAL',
        )
        validator = UniqueValueCheckValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )
        assert len(validator.errors) == 0
