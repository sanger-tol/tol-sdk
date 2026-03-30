# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from typing import Any

from werkzeug.datastructures import MultiDict

from .filter_utils import FilterUtils
from ...api_client.exception import BadPostJsonError
from ...core import DataSourceFilter


class AggregationArgs:
    """
    Parses the arguments for an Aggregation POST endpoint.
    These could come from the query string (request_args) or the POST body (body_dict).
    """

    __slots__ = ['__args_dict']
    __args_dict: dict

    # A number, then a word
    DATE_INTERVAL_REGEX = r'(\d+)([a-zA-Z]+)'
    # These units mean the same as they would in Elasticsearch aggregations. However, not all of
    # the units in Elastic are supported (just these ones below)
    DATE_INTERVAL_UNITS = 'd', 'w', 'M', 'y'

    def __init__(
        self,
        body_json: Any | None,
        request_args: MultiDict | None = None
    ) -> None:
        # Validate JSON body: must exist, and should be an object (not a list)
        # The accepted JSON body is an object (Python dict). It cannot be a list
        if not isinstance(body_json, dict):
            raise TypeError('JSON body must be an object')

        self.__args_dict = (
            (body_json if body_json else {})
            | (request_args.to_dict() if request_args else {})
        )

    # All args are calculated properties, because some args are required for one type of
    # aggregation, but not for others
    def __get_arg(
        self,
        arg_key: str,
        expected_type: type,  # (or None)
        default_value: Any | None = None
    ) -> Any:
        arg_value = self.__args_dict.get(arg_key)

        # The case that `None` was passed in or the arg wasn't supplied
        if arg_value is None:
            return default_value

        # Ensure the arg is the correct type
        if not isinstance(arg_value, expected_type):
            raise BadPostJsonError(
                arg_key,
                message=(
                    f'"{arg_key}" is of an incorrect type. '
                    f'Expected {expected_type}, found {type(arg_value)}'
                )
            )

        return arg_value

    @property
    def filter(self) -> DataSourceFilter | None:  # noqa A003
        filter_string: str | None = self.__get_arg('filter', str)

        if filter_string is None:
            return None
        else:
            return FilterUtils.parse_to_datasource_filter('filter', filter_string)

    @property
    def x_axis(self) -> str:
        return self.__get_arg('x_axis', str)

    @property
    def y_axis(self) -> str:
        return self.__get_arg('y_axis', str)

    @property
    def break_down_by(self) -> str:
        return self.__get_arg('break_down_by', str)

    @property
    def date_interval(self) -> str:
        interval_string = self.__get_arg('date_interval', str, '1M')

        # Validate the interval is a number and a unit
        match = re.search(AggregationArgs.DATE_INTERVAL_REGEX, interval_string)
        if not match:
            raise BadPostJsonError(
                'date_interval',
                message='Invalid format (expected value and unit, e.g. "1M")'
            )

        # Validate the unit is one of the accepted options
        unit = match.group(2)
        if unit not in AggregationArgs.DATE_INTERVAL_UNITS:
            raise BadPostJsonError(
                'date_interval',
                message=f'Invalid unit (expected one of {AggregationArgs.DATE_INTERVAL_UNITS})'
            )

        return interval_string

    @property
    def stat(self) -> str:
        return self.__get_arg('stat', str)

    @property
    def stat_field(self) -> str:
        return self.__get_arg('stat_field', str)

    @property
    def cumulative(self) -> bool:
        return self.__get_arg('cumulative', bool, False)

    @property
    def maximum_categories(self) -> int:
        return self.__get_arg('maximum_categories', int, 10)
