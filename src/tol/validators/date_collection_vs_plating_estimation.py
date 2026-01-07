# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import Validator
from tol.core.data_object import DataObject
import datetime


class DateCollectionVsPlatingEstimationValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) check the collection date
    is not preceding the plating date
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        collection: str
        plating: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function is used to check if the dates obtained 
        # are in the standard format and the date of collection 
        # is not preceding the date of plating

        collection_date = obj.attributes.get(self.__config.collection)
        plating_date = obj.attributes.get(self.__config.plating)

        if collection_date is not None:
            try:
                datetime.fromisoformat(collection_date)
            except ValueError:
                self.add_error(
                    object_id=obj.id,
                    detail=f'{self.__config.collection} is not in the right date format',
                    field=self.__config.collection,
                )
        if plating_date is not None:
            try:
                datetime.fromisoformat(plating_date)
            except ValueError:
                self.add_error(
                    object_id=obj.id,
                    detail=f'{self.__config.plating} is not in the right date format',
                    field=self.__config.plating,
                )
        if plating_date < collection_date:
            self.add_error(
                    object_id=obj.id,
                    detail=f'conflicting dates between {self.__config.plating} and {self.__config.collection}',
                    field=[self.__config.plating, self.__config.collection]
                )
