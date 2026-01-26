# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject, Validator
from tol.sources.goat import GoatDataSource, goat


class TaxonMatchesGoatValidator(Validator):
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
        
        if (scientific_name := obj.get_field_by_name('scientific_name')) != taxon.scientific_name:
            self.add_warning(
                object_id=obj.id,
                detail=(f'Scientific name {scientific_name} '
                        f'does not match scientific name of taxon ({taxon.scientific_name})')
            )
        
        self.__check_taxon_relationship(obj.id, obj.species, taxon.species, 'species')
        self.__check_taxon_relationship(obj.id, obj.genus, taxon.genus, 'genus')
        self.__check_taxon_relationship(obj.id, obj.family, taxon.family, 'family')
        self.__check_taxon_relationship(obj.id, obj.superfamily, taxon.superfamily, 'superfamily')
        self.__check_taxon_relationship(obj.id, obj.phylum, taxon.phylum, 'phylum')
        self.__check_taxon_relationship(obj.id, obj.kingdom, taxon.kingdom, 'kingdom')
        self.__check_taxon_relationship(obj.id, obj.superkingdom, taxon.superkingdom, 'superkingdom')
        self.__check_taxon_relationship(obj.id, obj.domain, taxon.domain, 'domain')
    
    def __check_taxon_relationship(self, obj_id, obj_relationship, taxon_value, relationship_name: str) -> None:
        if obj_relationship is None and taxon_value is None:
            return

        if obj_relationship is None and taxon_value is not None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'No value found for {relationship_name}, '
                        f'when GoaT has value {taxon_value}'),
                field=relationship_name,
            )
            return

        if obj_relationship is not None and taxon_value is None:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Unexpectedly found value for {relationship_name}, '
                        f'which is not found in GoaT'),
                field=relationship_name,
            )
            return
        
        if obj_relationship.scientific_name != taxon_value.scientific_name:
            self.add_warning(
                object_id=obj_id,
                detail=(f'Value for {relationship_name} ({obj_relationship.scientific_name}) '
                        f'does not match the value in GoaT ({taxon_value.scientific_name})')
            )
            return
