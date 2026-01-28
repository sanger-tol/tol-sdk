# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, Validator
from tol.sources.goat import GoatDataSource, goat


class TaxonMatchesGoatValidator(Validator):
    """
    Validates a stream of `DataObject` instances, checking whether its Taxonomy information
    matches that in GoaT
    """
    __slots__ = ['__goat_datasource', '_cached_taxa']
    __goat_datasource: GoatDataSource
    _cached_taxa: dict[str, DataObject]

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        # This validator doesn't need a config, but the flow needs it anyway
        pass

    def __init__(self) -> None:
        super().__init__()
        self.__goat_datasource = goat()
        self._cached_taxa = {}

    def _validate_data_object(self, obj: DataObject) -> None:
        taxon_id = obj.get_field_by_name('taxon_id')

        # Check whether we already have the information for this id in the cache.
        # If we don't, fetch it from GoaT and add it to the cache
        taxon: DataObject | None
        if taxon_id in self._cached_taxa:
            taxon = self._cached_taxa[taxon_id]
        else:
            taxon = self.__goat_datasource.get_one('taxon', taxon_id)

            # Add this taxon to cached taxa.
            # Error if GoaT has no taxon with this id
            if taxon is not None:
                self._cached_taxa[taxon_id] = taxon
            else:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Invalid Taxon ID: {taxon_id}',
                    field='taxon_id'
                )

                # We can't validate a taxon that doesn't exist, so after this error move on
                # to the next DataObject
                return

        # Check scientific name matches the one associated with the taxon id
        if (scientific_name := obj.get_field_by_name('scientific_name')) != taxon.scientific_name:
            self.add_warning(
                object_id=obj.id,
                detail=(f'Scientific name {scientific_name} '
                        f'does not match scientific name of taxon ({taxon.scientific_name})')
            )

        # Check all related taxons have the same scientific name as in GoaT
        self.__validate_taxon_rank(
            obj.id, obj.species, taxon.species, 'species'
        )
        self.__validate_taxon_rank(
            obj.id, obj.genus, taxon.genus, 'genus'
        )
        self.__validate_taxon_rank(
            obj.id, obj.family, taxon.family, 'family'
        )
        self.__validate_taxon_rank(
            obj.id, obj.superfamily, taxon.superfamily, 'superfamily'
        )
        self.__validate_taxon_rank(
            obj.id, obj.phylum, taxon.phylum, 'phylum'
        )
        self.__validate_taxon_rank(
            obj.id, obj.kingdom, taxon.kingdom, 'kingdom'
        )
        self.__validate_taxon_rank(
            obj.id, obj.superkingdom, taxon.superkingdom, 'superkingdom'
        )
        self.__validate_taxon_rank(
            obj.id, obj.domain, taxon.domain, 'domain'
        )

    def __validate_taxon_rank(
        self,
        obj_id: str | None,
        relationship_from_obj: DataObject | None,
        relationship_from_taxon_id: DataObject | None,
        taxon_rank_name: str,
    ) -> None:
        """
        A reusable function to perform the same validations for every taxon rank
        (e.g. kingdom, genus, species).
        It takes in the relationship to this taxon rank in the data object we're validating
        (relationship_from_obj) and the data object fetched from GoaT (relationship_from_taxon_id)
        """
        # Not every taxon has every taxon rank (e.g. it might not have a superkingdom).
        # In this case, the value in GoaT will be `None`. If so, the data object must also have
        # `None` for its value
        if relationship_from_taxon_id is None and relationship_from_obj is None:
            return

        # Check for the erronous case where the taxon rank does not exist for this taxon
        # (in GoaT), but the data object has a value for it anyway
        if relationship_from_taxon_id is None and relationship_from_obj is not None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Unexpectedly found value for {taxon_rank_name}, '
                        f'which is not found in GoaT'),
                field=taxon_rank_name,
            )
            return

        # Check for the data object missing the value for this taxon rank when it is present
        # in GoaT
        if relationship_from_taxon_id is not None and relationship_from_obj is None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'No value found for {taxon_rank_name}, '
                        f'when GoaT has value {relationship_from_taxon_id}'),
                field=taxon_rank_name,
            )
            return

        # Now we know there's a value for this taxon rank both in the data object and in GoaT,
        # so check whether they're the same
        if relationship_from_obj.scientific_name != relationship_from_taxon_id.scientific_name:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Value for {taxon_rank_name} ({relationship_from_obj.scientific_name}) '
                        f'does not match the value in GoaT '
                        f'({relationship_from_taxon_id.scientific_name})'),
                field=taxon_rank_name,
            )
            return
