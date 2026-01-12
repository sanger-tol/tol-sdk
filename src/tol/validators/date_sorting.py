# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import date, datetime

from tol.core import Validator
from tol.core.data_object import DataObject


class DateSortingValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) check the collection date
    is not preceding the plating date
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        dates: list[str]

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function is used to check if the dates obtained
        # are in the standard format and the date of collection
        # is not preceding the date of plating

        previous_date = None

        for date_field in self.__config.dates:
            date_value = obj.get_field_by_name(date_field)

            # Validate that the value is a date or datetime object
            if not isinstance(date_value, (date, datetime)):
                self.add_error(
                    object_id=obj.id,
                    detail=f'{date_field} of {date_value} is not in the right date format',
                    field=self.__config.dates,
                )
                return

            # Check if dates are in ascending order
            if previous_date is not None and date_value < previous_date:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Date {date_field} ({date_value})'
                    f'is before previous date ({previous_date})',
                    field=self.__config.dates,
                )
                return

            previous_date = date_value
