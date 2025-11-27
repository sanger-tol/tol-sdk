# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject
from tol.core.validate import Validator
from tol.core import DataSourceError, DataSourceFilter
from tol.sources.tolid import tolid


@dataclass
class TolidConfig:
    species_id_field: str
    specimen_id_field: str
    error_ignore_field: str
    error_ignore_value: str
    warning_detail: str = 'Species not found in Tol ID source'


class TolidValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique Tol IDs.
    """

    def __init__(
        self,
        config: TolidConfig,
        datasource=tolid(),
    ) -> None:

        super().__init__()

        self._datasource = datasource
        self._config = config
        self._cached_species_id = {}
        self._cached_tolids = {}

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        self._warning_on_species_not_in_tolid(obj=obj)
        self._error_on_specimen_id_and_taxon_not_matching_tolid(obj=obj)

    def _warning_on_species_not_in_tolid(
        self,
        obj: DataObject,
    ) -> None:

        obj_species_id = obj.get_field_by_name(self._config.species_id_field)
        if self._config.species_id_field in obj.attributes:
            try:
                if obj_species_id not in self._cached_species_id:
                    if self._datasource.get_one('species', obj_species_id) is not None:
                        self._cached_species_id[obj_species_id] = True
                    else:
                        self._cached_species_id[obj_species_id] = False

            except DataSourceError as e:
                if e.status_code == 404:
                    self._cached_species_id[obj_species_id] = False

        species_in_tolid = self._cached_species_id[obj_species_id]
        if species_in_tolid is False:
            self.add_warning(
                object_id=obj.id,
                detail=self._config.warning_detail,
                field=self._config.species_id_field,
            )

    def _error_on_specimen_id_and_taxon_not_matching_tolid(
        self,
        obj: DataObject,
    ) -> None:

        if (obj.get_field_by_name(self._config.error_ignore_field) is 
                self._config.error_ignore_value):
            return

        if self._config.specimen_id_field in obj.attributes:
            specimen_id = obj.get_field_by_name(self._config.specimen_id_field)
            if specimen_id not in self._cached_tolids:
                f = DataSourceFilter()
                f.and_ = {'specimen_id': {'eq': {'value': specimen_id}}}
                self._cached_tolids[specimen_id] = list(self._datasource.get_list(
                    object_type='specimen',
                    filters=f
                ))

            if (len(self._cached_tolids[specimen_id]) == 0):
                return
            else:
                taxons = set()
                for tolid_ in self._cached_tolids[specimen_id]:
                    taxons.add(str(tolid_.species.id))

                if str(obj.get_field_by_name(self._config.species_id_field)) not in taxons:
                    self.add_error(
                        object_id=obj.id,
                        detail=f'Specimen ID {specimen_id} does not match Taxon ID '
                               f'{obj.get_field_by_name(self._config.species_id_field)}'
                               'in TolID source',
                        field=[self._config.specimen_id_field, self._config.species_id_field]
                    )
