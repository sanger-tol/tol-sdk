# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime

from tol.core import Validator
from tol.core.data_object import DataObject


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

        collection_value = obj.attributes.get(self.__config.collection)
        plating_value = obj.attributes.get(self.__config.plating)

        collection_date = None
        plating_date = None

        # Validate collection date format
        if collection_value is not None:
            try:
                collection_date = datetime.fromisoformat(collection_value)
            except ValueError:
                self.add_error(
                    object_id=obj.id,
                    detail=f'{self.__config.collection} is not in the right date format',
                    field=self.__config.collection,
                )
                return  # Skip comparison if format is invalid

        # Validate plating date format
        if plating_value is not None:
            try:
                plating_date = datetime.fromisoformat(plating_value)
            except ValueError:
                self.add_error(
                    object_id=obj.id,
                    detail=f'{self.__config.plating} is not in the right date format',
                    field=self.__config.plating,
                )
                return  # Skip comparison if format is invalid

        # Compare dates if both are valid
        if collection_date is not None and plating_date is not None:
            if collection_date > plating_date:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Collection date ({collection_date})'
                    f'is after plating date ({plating_date})',
                    field=[self.__config.collection, self.__config.plating],
                )
