# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import create_autospec, patch

from tol.core import DataObject
from tol.sources.goat import GoatDataSource
from tol.validators import TaxonMatchesGoatValidator


class TestTaxonMatchesGoatValidator:
    def test_valid(
        self,
        mock_objs: Iterable[DataObject],
    ) -> None:
        """
        Validates two data objects that have correct matching data with GoaT
        """
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '6344'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        mock_two = create_autospec(DataObject)
        mock_two.id = 'b'

        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '9631'
                case 'SCIENTIFIC_NAME':
                    return 'Vulpes velox'
                case 'GENUS':
                    return 'Vulpes'
                case 'FAMILY':
                    return 'Canidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Chordata'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
        )

        validator = TaxonMatchesGoatValidator(config)

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
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '6344'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        mock_two = create_autospec(DataObject)
        mock_two.id = 'b'

        def __get_field_by_name_two(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '6344'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_two.get_field_by_name.side_effect = __get_field_by_name_two

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
        )

        validator = TaxonMatchesGoatValidator(config)
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

    def test_invalid_taxon_id(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Ensures that attempting to validate a data object with an invalid Taxon ID will result
        in an error
        """
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '-1'  # invalid taxon id
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
        )

        validator = TaxonMatchesGoatValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one]))
        )

        # Expect there to be an error for the invalid taxon_id
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0

    def test_skipped_rank(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Ensures that a rank not provided in the validator config is not checked
        """
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '6344'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return 'INVALID'
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
        )

        validator = TaxonMatchesGoatValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one]))
        )

        # There shouldn't be a warning for the invalid superfamily (which should be None),
        # because superfamily isn't set in the config
        assert len(validator.results) == 0

    def test_taxon_rank_does_not_match(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Ensures that a warning will be raised if a taxon rank has a value different to in GoaT
        """
        # The provided mock objects are not appropriate for this test, so we set up new ones
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '6344'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'INVALID'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return None
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
        )

        validator = TaxonMatchesGoatValidator(config)

        # consume the `Iterable`
        list(
            validator.validate(iter([mock_one]))
        )

        # Expect there to be a warning for the incorrect genus
        assert len(validator.warnings) == 1
        assert len(validator.errors) == 0

    def test_exempt_taxon_ids_pass_regardless_of_goat_data(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:
        """
        Ensures an exempt taxon ID produces no warnings or errors
        and is not queried from GoaT
        """
        del mock_objs
        mock_one = create_autospec(DataObject)
        mock_one.id = 'a'

        def __get_field_by_name_one(name: str) -> Any:
            match name:
                case 'TAXON_ID':
                    return '32644'
                case 'SCIENTIFIC_NAME':
                    return 'Arenicola marina'
                case 'GENUS':
                    return 'Arenicola'
                case 'FAMILY':
                    return 'Arenicolidae'
                case 'SUPERFAMILY':
                    return 'INVALID'
                case 'PHYLUM':
                    return 'Annelida'
                case 'KINGDOM':
                    return 'Metazoa'
                case 'SUPERKINGDOM':
                    return None
                case 'DOMAIN':
                    return 'Eukaryota'
        mock_one.get_field_by_name.side_effect = __get_field_by_name_one

        config = TaxonMatchesGoatValidator.Config(
            species_field='SCIENTIFIC_NAME',
            genus_field='GENUS',
            family_field='FAMILY',
            exempt_taxon_ids=['32644']
        )

        mock_goat = create_autospec(GoatDataSource, instance=True)

        with patch(
            'tol.validators.taxon_matches_goat.goat',
            return_value=mock_goat
        ):
            validator = TaxonMatchesGoatValidator(config)

            list(
                validator.validate(iter([mock_one]))
            )

        # Expect there to be no warnings or errors for a taxon_id not found in GoaT
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 0
        mock_goat.get_one.assert_not_called()
