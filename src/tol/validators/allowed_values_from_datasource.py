# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, DataSourceUtils
from tol.core.validate import Validator
from tol.sources.portaldb import portaldb


class AllowedValuesFromDataSourceValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains field that is part of a list.
    """

    @dataclass
    class Config:
        datasource_instance_id: int
        datasource_object_type: str
        datasource_field_name: str
        field_name: str

    def __init__(
        self,
        config: Config,
        allowed_values: list[str | int | float] | None = None,  # For testing
    ) -> None:

        super().__init__()

        self._config = config
        if allowed_values is None:
            self.__cached_list = self.__initialize_list_from_datasource()
        else:
            self.__cached_list = allowed_values

    def __initialize_list_from_datasource(self) -> list[str | int | float]:
        dsi = portaldb().get_one('data_source_instance', self._config.datasource_instance_id)
        ds = DataSourceUtils.get_data_source_by_data_source_instance(dsi)
        self._cached_list = [
            obj.get_field_by_name(
                self._config.datasource_field_name
            ) for obj in ds.get_list(
                object_type=self._config.datasource_object_type
            )
        ]

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        field_value = obj.get_field_by_name(self._config.field_name)
        if field_value not in self.__cached_list:
            self.add_error(
                object_id=obj.id,
                detail=f'Field {self._config.field_name} value '
                       f'"{field_value}" not found in list '
                       f'{self.__cached_list}',
                field=self._config.field_name,
            )
