# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject, Validator
from tol.sources.goat import goat, GoatDataSource


class TaxonMatchesGoatValidator(Validator):
    __slots__ = ["__goat_datasource", "__cached_taxons"]
    __goat_datasource: GoatDataSource
    __cached_taxons: dict[str, DataObject]

    def __init__(self) -> None:
        super().__init__()
        self.__goat_datasource = goat()
        self.__cached_taxons = {}
    
    def _validate_data_object(self, obj: DataObject) -> None:
        taxon_id = obj.get_field_by_name("taxon_id")

        # Check whether we already have the information for this id in the cache.
        # If we don't, fetch it from GOAT and add it to the cache
        taxon: DataObject | None
        if taxon_id in self.__cached_taxons:
            taxon = self.__cached_taxons[taxon_id]
        else:
            taxon = self.__goat_datasource.get_one("taxon", taxon_id)
            if taxon is None:
                self.add_error(
                    object_id=obj.id,
                    detail="Invalid TaxonID: " + taxon_id,
                    field="taxon_id"
                )
