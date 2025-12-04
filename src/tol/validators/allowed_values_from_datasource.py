# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import DataObject, DataSourceUtils
from tol.core.validate import Validator
from tol.sources.portaldb import portaldb


class AllowedValuesFromDataSourceValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains field that is part of a list.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        allowed_values: List[str | int | float] | None = None
        datasource_instance_id: int
        datasource_object_type: str
        datasource_field_name: str
        field_name: str

    __slots__ = ['__config', '__cached_list']
    __config: Config
    __cached_list: List[str | int | float]

    def __init__(
        self,
        config: Config,
    ) -> None:

        super().__init__()

        self.__config = config
        self.__cached_list = self.__config.allowed_values \
            or self.__initialize_list_from_datasource()

        if self.__config.allowed_values is None:
            self.__cached_list = self.__initialize_list_from_datasource()
        else:
            self.__cached_list = self.__config.allowed_values

    def __initialize_list_from_datasource(self) -> List[str | int | float]:
        dsi = portaldb().get_one('data_source_instance', self.__config.datasource_instance_id)
        ds = DataSourceUtils.get_data_source_by_data_source_instance(dsi)
        return [
            obj.get_field_by_name(
                self.__config.datasource_field_name
            ) for obj in ds.get_list(
                object_type=self.__config.datasource_object_type
            )
        ]

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        field_value = obj.get_field_by_name(self.__config.field_name)
        if field_value not in self.__cached_list:
            print(self.__cached_list)
            multiple_cached_values = len(self.__cached_list) > 1

            cached_list_str = ''
            if multiple_cached_values:
                for index, field in enumerate(self.__cached_list):
                    if index == 0:
                        # First item in the list
                        cached_list_str += f'{field}'
                    elif index == len(self.__cached_list) - 1:
                        # Last item in the list
                        cached_list_str += f' or {field}'
                    else:
                        # Middle items
                        cached_list_str += f', {field}'
            else:  # Only one field
                cached_list_str = self.__cached_list[0]

            self.add_error(
                object_id=obj.id,
                detail=f'The value of the field {self.__config.field_name} '
                       f'must be{' one of' if multiple_cached_values else ''} {cached_list_str} '
                       f'(found value {field_value})',
                field=self.__config.field_name,
            )
