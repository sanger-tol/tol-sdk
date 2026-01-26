# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.validators.taxon_matches_goat import TaxonMatchesGoatValidator


class TestTaxonMatchesGoatValidator:
    def test_validator_cached(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Uses two data objects that have the same value for their key column. Tests whether the
        validator used for the second data object is the same as the one used for the first.
        """
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'Arenicola marina'
        mock_one.taxon_id = '6344'
        mock_one.species.scientific_name = 'Arenicola'
        mock_one.genus.scientific_name = 'Arenicolidae'
        mock_one.family.scientific_name = 'Arenicolidae'
        mock_one.superfamily.scientific_name = None
        mock_one.phylum.scientific_name = 'Annelida'
        mock_one.kingdom.scientific_name = 'Metazoa'
        mock_one.superkingdom.scientific_name = None
        mock_one.domain.scientific_name = 'Eukaryota'
        mock_two = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'Arenicola marina'
        mock_two.taxon_id = '6344'
        mock_two.species.scientific_name = 'Arenicola'
        mock_two.genus.scientific_name = 'Arenicolidae'
        mock_two.family.scientific_name = 'Arenicolidae'
        mock_two.superfamily.scientific_name = None
        mock_two.phylum.scientific_name = 'Annelida'
        mock_two.kingdom.scientific_name = 'Metazoa'
        mock_two.superkingdom.scientific_name = None
        mock_two.domain.scientific_name = 'Eukaryota'

        validator = TaxonMatchesGoatValidator()
        validations = iter(validator.validate(iter([mock_one, mock_two])))

        # Validate the first object and get a reference to the taxon object
        next(validations)
        assert len(validator._cached_taxa) == 1
        taxon_object_one = validator._cached_taxa.get('6344')
        assert taxon_object_one is not None

        # Validate the second object and get a reference to the taxon object
        next(validations)
        assert len(validator._cached_taxa) == 1
        taxon_object_two = validator._cached_taxa.get('6344')
        assert taxon_object_two is not None

        # Check they're the same object
        assert taxon_object_one == taxon_object_two
