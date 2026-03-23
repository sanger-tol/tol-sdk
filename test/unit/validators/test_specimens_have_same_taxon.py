# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators import SpecimensHaveSameTaxonValidator


class TestSpecimensHaveSameTaxonValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SPECIMEN_ID': 'A',
            'TAXON_ID': 'AA'
        }
        mock_one.SPECIMEN_ID = 'A'
        mock_one.TAXON_ID = 'AA'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'SPECIMEN_ID': 'A',
            'TAXON_ID': 'AA'
        }
        mock_one.SPECIMEN_ID = 'A'
        mock_one.TAXON_ID = 'AA'

        config = SpecimensHaveSameTaxonValidator.Config(
            taxon_id_field='TAXON_ID',
            symbiont_field='SYMBIONT',
            specimen_id_field='SPECIMEN_ID',
        )
        validator = SpecimensHaveSameTaxonValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert not validator.results

    def test_clash_specimen_diff_taxon(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        # Discard the sample mock objects (which won't be useful for this test)
        del mock_objs
        mock_one: DataObject = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.attributes = {
            'SPECIMEN_ID': 'A',
            'TAXON_ID': 'AA'
        }
        mock_one.SPECIMEN_ID = 'A'
        mock_one.TAXON_ID = 'AA'
        mock_two: DataObject = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.attributes = {
            'SPECIMEN_ID': 'A',
            'TAXON_ID': 'AB'
        }
        mock_one.SPECIMEN_ID = 'A'
        mock_one.TAXON_ID = 'AB'

        config = SpecimensHaveSameTaxonValidator.Config(
            taxon_id_field='TAXON_ID',
            symbiont_field='SYMBIONT',
            specimen_id_field='SPECIMEN_ID',
        )
        validator = SpecimensHaveSameTaxonValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.errors) == 1
