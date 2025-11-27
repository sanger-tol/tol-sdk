# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core.validate import Validator
from tol.sources.tolid import tolid
from tol.core import DataSourceError, DataSourceFilter


class TolidValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique Tol IDs.
    """

    def __init__(
        self,
        species_attribute: str,
        error_ignore_field: str,
        error_ignore_value: str,
        specimen_attribute: str,
        datasource = tolid(),
        warning_detail: str = 'Species not found in Tol ID source',
    ) -> None:

        super().__init__()

        self._species_attribute = species_attribute
        self._datasource = datasource
        self._warning_detail = warning_detail
        self._error_ignore_field = error_ignore_field
        self._error_ignore_value = error_ignore_value
        self._specimen_attribute = specimen_attribute
        self._cached_species_id = {}
        self._cached_tolids = {}
        
    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        # self._warning_on_species_not_in_tolid(obj=obj)
        self._error_on_specimen_id_and_taxon_not_matching_tolid(obj=obj)

    def _warning_on_species_not_in_tolid(
        self,
        obj: DataObject,
    ) -> None:

        obj_species_id = obj.get_field_by_name(self._species_attribute)
        if self._species_attribute in obj.attributes:
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
        if species_in_tolid == False:
            self.add_warning(
                object_id=obj.id,
                detail=self._warning_detail,
                field=self._species_attribute
            )
            
    def _error_on_specimen_id_and_taxon_not_matching_tolid(
        self,
        obj: DataObject,
    ) -> None:
        
        if obj.get_field_by_name(self._error_ignore_field) is self._error_ignore_value:
            return

        if self._specimen_attribute in obj.attributes:
            specimen_id = obj.get_field_by_name(self._specimen_attribute)
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
                if str(obj.get_field_by_name(self._species_attribute)) not in taxons:
                    self.add_error(
                        object_id=obj.id,
                        detail=f"Specimen ID {specimen_id} does not match Taxon ID {obj.get_field_by_name(self._species_attribute)} in TolID source",
                        field=[self._specimen_attribute, self._species_attribute]
                    )
                