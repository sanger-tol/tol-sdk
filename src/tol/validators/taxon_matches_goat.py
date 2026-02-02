# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, Validator
from tol.sources.goat import ElasticDataSource, goat


class TaxonMatchesGoatValidator(Validator):
    """
    Validates a stream of `DataObject` instances, checking whether its Taxonomy information
    matches that in GoaT
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        species_field: str | None = None
        genus_field: str | None = None
        family_field: str | None = None
        superfamily_field: str | None = None
        phylum_field: str | None = None
        kingdom_field: str | None = None
        superkingdom_field: str | None = None
        domain_field: str | None = None

    __slots__ = ['__config', '__goat_datasource', '_cached_taxa']
    __config: Config
    __goat_datasource: ElasticDataSource
    _cached_taxa: dict[str, DataObject]

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config
        self.__goat_datasource = goat()
        self._cached_taxa = {}

    def _validate_data_object(self, obj: DataObject) -> None:
        taxon_id = obj.get_field_by_name('TAXON_ID')

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

        # Check that each associated taxonomy rank for this taxon matches those in GoaT
        taxonomic_ranks = ('species', 'genus', 'family', 'superfamily',
                           'phylum', 'kingdom', 'superkingdom', 'domain')
        for rank in taxonomic_ranks:
            # From the rank to check, get the name of its field in the data object we're validating
            # from the validator config. If this field name is `None`, then this taxonomic rank
            # isn't being checked (likely because the data object does not have this field)
            field_name: str | None = getattr(self.__config, f'{rank}_field')
            if field_name is None:
                continue

            # Fetch the values of these taxonomic ranks
            value_in_data_object = obj.get_field_by_name(field_name)
            value_in_goat = taxon.get_field_by_name(f'{rank}.scientific_name')

            # Ensure the value in the data object matches the one in GoaT
            if value_in_data_object != value_in_goat:
                self.add_warning(
                    object_id=obj.id,
                    detail=(f'Value for {field_name} ({value_in_data_object}) '
                            f'does not match the value in GoaT ({value_in_goat})'),
                    field=field_name,
                )
