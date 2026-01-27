# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec, PropertyMock

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
        class DummyScientificName:
            __slots__ = ['scientific_name']

            def __init__(self, scientific_name) -> None:
                self.scientific_name = scientific_name

        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'
        mock_one.get_field_by_name.return_value = 'Arenicola marina'
        mock_one.attributes['taxon_id'] = '6344'
        type(mock_one).species = PropertyMock(return_value=DummyScientificName('Arenicola marina'))
        type(mock_one).genus = PropertyMock(return_value=DummyScientificName('Arenicolidae'))
        type(mock_one).family = PropertyMock(return_value=DummyScientificName('Arenicolidae'))
        type(mock_one).superfamily = PropertyMock(return_value=DummyScientificName(None))
        type(mock_one).phylum = PropertyMock(return_value=DummyScientificName('Annelida'))
        type(mock_one).kingdom = PropertyMock(return_value=DummyScientificName('Metazoa'))
        type(mock_one).superkingdom = PropertyMock(return_value=DummyScientificName(None))
        type(mock_one).domain = PropertyMock(return_value=DummyScientificName('Eukaryota'))
        mock_two = create_autospec(DataObject)
        mock_two.id = 'b'
        mock_two.get_field_by_name.return_value = 'Arenicola marina'
        mock_two.attributes['taxon_id'] = '6344'
        type(mock_two).species = PropertyMock(return_value=DummyScientificName('Arenicola marina'))
        type(mock_two).genus = PropertyMock(return_value=DummyScientificName('Arenicolidae'))
        type(mock_two).family = PropertyMock(return_value=DummyScientificName('Arenicolidae'))
        type(mock_two).superfamily = PropertyMock(return_value=DummyScientificName(None))
        type(mock_two).phylum = PropertyMock(return_value=DummyScientificName('Annelida'))
        type(mock_two).kingdom = PropertyMock(return_value=DummyScientificName('Metazoa'))
        type(mock_two).superkingdom = PropertyMock(return_value=DummyScientificName(None))
        type(mock_two).domain = PropertyMock(return_value=DummyScientificName('Eukaryota'))

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
