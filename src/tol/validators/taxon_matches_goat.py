# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject, Validator
from tol.sources.goat import GoatDataSource, goat


class TaxonMatchesGoatValidator(Validator):
    """
    TODO
    """
    __slots__ = ['__goat_datasource', '__cached_taxons']
    __goat_datasource: GoatDataSource
    __cached_taxons: dict[str, DataObject]

    def __init__(self) -> None:
        super().__init__()
        self.__goat_datasource = goat()
        self.__cached_taxons = {}

    def _validate_data_object(self, obj: DataObject) -> None:
        taxon_id = obj.get_field_by_name('taxon_id')

        # Check whether we already have the information for this id in the cache.
        # If we don't, fetch it from GoaT and add it to the cache
        taxon: DataObject | None
        if taxon_id in self.__cached_taxons:
            taxon = self.__cached_taxons[taxon_id]
        else:
            taxon = self.__goat_datasource.get_one('taxon', taxon_id)

            # Error if GoaT has no taxon with this id
            if taxon is None:
                self.add_error(
                    object_id=obj.id,
                    detail='Invalid TaxonID: ' + taxon_id,
                    field='taxon_id'
                )

        # Check scientific name matches the one associated with the taxon id
        if (scientific_name := obj.get_field_by_name('scientific_name')) != taxon.scientific_name:
            self.add_warning(
                object_id=obj.id,
                detail=(f'Scientific name {scientific_name} '
                        f'does not match scientific name of taxon ({taxon.scientific_name})')
            )

        # Check all related taxons have the same scientific name as in GoaT
        self.__check_taxon_relationship(
            obj.id, obj.species, taxon.species, 'species'
        )
        self.__check_taxon_relationship(
            obj.id, obj.genus, taxon.genus, 'genus'
        )
        self.__check_taxon_relationship(
            obj.id, obj.family, taxon.family, 'family'
        )
        self.__check_taxon_relationship(
            obj.id, obj.superfamily, taxon.superfamily, 'superfamily'
        )
        self.__check_taxon_relationship(
            obj.id, obj.phylum, taxon.phylum, 'phylum'
        )
        self.__check_taxon_relationship(
            obj.id, obj.kingdom, taxon.kingdom, 'kingdom'
        )
        self.__check_taxon_relationship(
            obj.id, obj.superkingdom, taxon.superkingdom, 'superkingdom'
        )
        self.__check_taxon_relationship(
            obj.id, obj.domain, taxon.domain, 'domain'
        )

    def __check_taxon_relationship(
        self,
        obj_id: str | None,
        relationship_from_obj: DataObject | None,
        relationship_from_taxon_id: DataObject | None,
        relationship_name: str,  # Name of lineage item
    ) -> None:
        # Not every taxon has every lineage item (e.g. it might not have a superkingdom).
        # In this case, the value in GoaT will be `None`. If so, the data object must also have
        # `None` for its value
        if relationship_from_taxon_id is None and relationship_from_obj is None:
            return

        # Check for the erronous case where the lineage item does not exist for this taxon
        # (in GoaT), but the data object has a value for it anyway
        if relationship_from_taxon_id is None and relationship_from_obj is not None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Unexpectedly found value for {relationship_name}, '
                        f'which is not found in GoaT'),
                field=relationship_name,
            )
            return

        # Check for the data object missing the value for this lineage item when it is present
        # in GoaT
        if relationship_from_taxon_id is not None and relationship_from_obj is None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'No value found for {relationship_name}, '
                        f'when GoaT has value {relationship_from_taxon_id}'),
                field=relationship_name,
            )
            return
        
        # Now we know there's a value for this lineage item both in the data object and in GoaT,
        # so check whether they're the same
        if relationship_from_obj.scientific_name != relationship_from_taxon_id.scientific_name:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Value for {relationship_name} ({relationship_from_obj.scientific_name}) '
                        f'does not match the value in GoaT '
                        f'({relationship_from_taxon_id.scientific_name})')
            )
            return
