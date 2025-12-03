# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, DataSource
from tol.core.validate import Validator
from tol.sources.ena import ena


class EnaSubmittableValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains field that is part of a list.
    """

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field_name: str

    def __init__(
        self,
        config: Config,
        ena_datasource: DataSource | None = ena(),  # For testing
    ) -> None:

        super().__init__()

        self._config = config
        self.__cached_species = {}
        self.__ena_datasource = ena_datasource

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        taxon_id = obj.get_field_by_name(self._config.field_name)
        if taxon_id not in self.__cached_species:
            ena_taxon = self.__ena_datasource.get_one('submittable_taxon', taxon_id)
            if ena_taxon:
                self.__cached_species[taxon_id] = ena_taxon
        if taxon_id not in self.__cached_species:
            self.add_error(
                object_id=obj.id,
                detail=f'Field {self._config.field_name} value '
                       f'"{taxon_id}" not found in ENA',
                field=self._config.field_name,
            )
        elif not self.__cached_species[taxon_id].submittable:
            self.add_error(
                object_id=obj.id,
                detail=f'Field {self._config.field_name} value '
                       f'"{taxon_id}" is not submittable in ENA',
                field=self._config.field_name,
            )
