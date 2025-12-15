# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict

from tol.core import DataObject, DataSource
from tol.core import DataSourceError, DataSourceFilter
from tol.core.validate import Validator
from tol.sources.tolid import tolid


class TolidValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique Tol IDs.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        species_id_field: str
        specimen_id_field: str
        error_ignore_field: str
        error_ignore_value: str
        warning_detail: str = 'Species not found in Tol ID source'

    __slots__ = ['__config', '__datasource', '__cached_species_id', '__cached_tolids']
    __config: Config
    __datasource: DataSource
    __cached_species_ids: Dict[str, Any]
    __cached_tolids: Dict[str, Any]

    def __init__(
        self,
        config: Config,
        datasource=tolid(),
        **kwargs
    ) -> None:

        super().__init__()

        self.__config = config
        self.__datasource = datasource
        self.__cached_species_ids = {}
        self.__cached_tolids = {}

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        self.__warning_on_species_not_in_tolid(obj=obj)
        self.__error_on_specimen_id_and_taxon_not_matching_tolid(obj=obj)

    def __warning_on_species_not_in_tolid(
        self,
        obj: DataObject,
    ) -> None:

        obj_species_id = obj.get_field_by_name(self.__config.species_id_field)
        if self.__config.species_id_field in obj.attributes:
            try:
                if obj_species_id not in self.__cached_species_ids:
                    self.__cached_species_ids[obj_species_id] = (
                        self.__datasource.get_one('species', obj_species_id) is not None)

            except DataSourceError as e:
                if e.status_code == 404:
                    self.__cached_species_ids[obj_species_id] = False

        species_in_tolid = self.__cached_species_ids[obj_species_id]
        if species_in_tolid is False:
            self.add_warning(
                object_id=obj.id,
                detail=self.__config.warning_detail,
                field=self.__config.species_id_field,
            )

    def __error_on_specimen_id_and_taxon_not_matching_tolid(
        self,
        obj: DataObject,
    ) -> None:

        if (obj.get_field_by_name(self.__config.error_ignore_field) is
                self.__config.error_ignore_value):
            return

        if self.__config.specimen_id_field in obj.attributes:
            specimen_id = obj.get_field_by_name(self.__config.specimen_id_field)
            if specimen_id not in self.__cached_tolids:
                f = DataSourceFilter()
                f.and_ = {'specimen_id': {'eq': {'value': specimen_id}}}
                self.__cached_tolids[specimen_id] = list(self.__datasource.get_list(
                    object_type='specimen',
                    object_filters=f
                ))

            if (len(self.__cached_tolids[specimen_id]) == 0):
                return
            else:
                taxons = set()
                for tolid_ in self.__cached_tolids[specimen_id]:
                    taxons.add(str(tolid_.species.id))

                if str(obj.get_field_by_name(self.__config.species_id_field)) not in taxons:
                    self.add_error(
                        object_id=obj.id + 1,
                        detail=f'Specimen ID {specimen_id} does not match Taxon ID '
                               f'{obj.get_field_by_name(self.__config.species_id_field)}'
                               'in TolID source',
                        field=[self.__config.specimen_id_field, self.__config.species_id_field]
                    )
