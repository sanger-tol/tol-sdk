# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core.validate import Validator
from tol.sources.tolid import tolid
from tol.core import DataSourceError


class TolidValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique Tol IDs.
    """

    def __init__(
        self,
        species_attribute: str,
        datasource = tolid(),
        warning_detail: str = 'Species not found in Tol ID source',
    ) -> None:

        super().__init__()

        self._species_attribute = species_attribute
        self._responses = {}
        self._datasource = datasource
        self._warning_detail = warning_detail
        
    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        self._warning_on_species_not_in_tolid(obj=obj)

    def _warning_on_species_not_in_tolid(
        self,
        obj: DataObject,
    ) -> None:

        obj_species_id = obj.get_field_by_name(self._species_attribute)
        if self._species_attribute in obj.attributes:
            try:
                if obj_species_id not in self._responses:
                    if self._datasource.get_one('species', obj_species_id) != None:
                        self._responses[obj_species_id] = True
                    else:
                        self._responses[obj_species_id] = False
                
            except DataSourceError as e:
                if e.status_code == 404:
                    self._responses[obj_species_id] = False

        species_in_tolid = self._responses[obj_species_id]
        if species_in_tolid == False:
            self.add_warning(
                object_id=obj.id,
                detail=self._warning_detail,
                field=self._species_attribute
            )