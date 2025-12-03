# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import UniqueWholeOrganismsValidator


class TestUniqueWholeOrganismsValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'ORGANISM_PART': 'WHOLE_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_one.ORGANISM_PART = 'WHOLE_ORGANISM'
        mock_one.SPECIMEN_ID = 'one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'ORGANISM_PART': 'PART_ORGANISM',
            'SPECIMEN_ID': 'two',
        }
        mock_two.ORGANISM_PART = 'PART_ORGANISM'
        mock_two.SPECIMEN_ID = 'two'

        config = UniqueWholeOrganismsValidator.Config(
            symbiont_field='SYMBIONT',
            organism_part_field='ORGANISM_PART',
            specimen_id_field='SPECIMEN_ID',
        )

        validator = UniqueWholeOrganismsValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert not validator.results

    def test_whole_organisms_clash(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'ORGANISM_PART': 'WHOLE_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_one.ORGANISM_PART = 'WHOLE_ORGANISM'
        mock_one.SPECIMEN_ID = 'one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'ORGANISM_PART': 'WHOLE_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_two.ORGANISM_PART = 'WHOLE_ORGANISM'
        mock_two.SPECIMEN_ID = 'one'

        config = UniqueWholeOrganismsValidator.Config(
            symbiont_field='SYMBIONT',
            organism_part_field='ORGANISM_PART',
            specimen_id_field='SPECIMEN_ID',
        )

        validator = UniqueWholeOrganismsValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1

    def test_whole_organism_then_part_organism_with_same_specimen_id(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'ORGANISM_PART': 'WHOLE_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_one.ORGANISM_PART = 'WHOLE_ORGANISM'
        mock_one.SPECIMEN_ID = 'one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'ORGANISM_PART': 'PART_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_two.ORGANISM_PART = 'PART_ORGANISM'
        mock_two.SPECIMEN_ID = 'one'

        config = UniqueWholeOrganismsValidator.Config(
            symbiont_field='SYMBIONT',
            organism_part_field='ORGANISM_PART',
            specimen_id_field='SPECIMEN_ID',
        )

        validator = UniqueWholeOrganismsValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1

    def test_part_organism_then_whole_organism_with_same_specimen_id(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'ORGANISM_PART': 'PART_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_one.ORGANISM_PART = 'PART_ORGANISM'
        mock_one.SPECIMEN_ID = 'one'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'ORGANISM_PART': 'WHOLE_ORGANISM',
            'SPECIMEN_ID': 'one',
        }
        mock_two.ORGANISM_PART = 'WHOLE_ORGANISM'
        mock_two.SPECIMEN_ID = 'one'

        config = UniqueWholeOrganismsValidator.Config(
            symbiont_field='SYMBIONT',
            organism_part_field='ORGANISM_PART',
            specimen_id_field='SPECIMEN_ID',
        )

        validator = UniqueWholeOrganismsValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1
