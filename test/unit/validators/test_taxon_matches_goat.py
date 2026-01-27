# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import PropertyMock, create_autospec

from tol.core import DataObject
from tol.validators.taxon_matches_goat import TaxonMatchesGoatValidator


class TestTaxonMatchesGoatValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Validates two data objects that have correct matching data with GoaT
        """
        class DummyScientificName:
            """
            Used to mock the scientific_name field for related data objects to the returned taxon
            """
            __slots__ = ['scientific_name']
            scientific_name: str

            def __init__(self, scientific_name) -> None:
                self.scientific_name = scientific_name

        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'
        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'taxon_id':
                    return '6344'
                case 'scientific_name':
                    return 'Arenicola marina'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one
        type(mock_one).species = PropertyMock(return_value=DummyScientificName('Arenicola marina'))
        type(mock_one).genus = PropertyMock(return_value=DummyScientificName('Arenicola'))
        type(mock_one).family = PropertyMock(return_value=DummyScientificName('Arenicolidae'))
        type(mock_one).superfamily = PropertyMock(return_value=DummyScientificName(None))
        type(mock_one).phylum = PropertyMock(return_value=DummyScientificName('Annelida'))
        type(mock_one).kingdom = PropertyMock(return_value=DummyScientificName('Metazoa'))
        type(mock_one).superkingdom = PropertyMock(return_value=DummyScientificName(None))
        type(mock_one).domain = PropertyMock(return_value=DummyScientificName('Eukaryota'))
        mock_two = create_autospec(DataObject)
        mock_two.id = 'b'
        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'taxon_id':
                    return '9631'
                case 'scientific_name':
                    return 'Vulpes velox'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two
        type(mock_two).species = PropertyMock(return_value=DummyScientificName('Vulpes velox'))
        type(mock_two).genus = PropertyMock(return_value=DummyScientificName('Vulpes'))
        type(mock_two).family = PropertyMock(return_value=DummyScientificName('Canidae'))
        type(mock_two).superfamily = PropertyMock(return_value=DummyScientificName(None))
        type(mock_two).phylum = PropertyMock(return_value=DummyScientificName('Chordata'))
        type(mock_two).kingdom = PropertyMock(return_value=DummyScientificName('Metazoa'))
        type(mock_two).superkingdom = PropertyMock(return_value=DummyScientificName(None))
        type(mock_two).domain = PropertyMock(return_value=DummyScientificName('Eukaryota'))

        validator = TaxonMatchesGoatValidator()

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one, mock_two]))
        )

        assert len(validator.results) == 0

    def test_validator_cached(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Uses two data objects that have the same value for their key column. Tests whether the
        validator used for the second data object is the same as the one used for the first.
        """
        class DummyScientificName:
            """
            Used to mock the scientific_name field for related data objects to the returned taxon
            """
            __slots__ = ['scientific_name']
            scientific_name: str

            def __init__(self, scientific_name) -> None:
                self.scientific_name = scientific_name

        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'
        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'taxon_id':
                    return '6344'
                case 'scientific_name':
                    return 'Arenicola marina'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one
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
        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'taxon_id':
                    return '6344'
                case 'scientific_name':
                    return 'Arenicola marina'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two
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
