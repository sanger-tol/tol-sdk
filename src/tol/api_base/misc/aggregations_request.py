# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...api_client.exception import BadPostJsonError
from .filter_utils import FilterUtils


class AggregationParameters:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    __slots__ = ['__request_args']
    __request_args: dict[str, str]

    def __init__(self, request_args: dict[str, str]) -> None:
        self.__request_args = request_args

    @property
    def filter(self) -> str | None:  # noqa A003
        """
        The optional filter JSON string.
        """
        filter_string = self.__request_args.get('filter')
        if filter_string is None:
            return None

        return FilterUtils.parse_to_datasource_filter('filter', filter_string)


class AggregationBody:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    __slots__ = ['__body_dict']
    __body_dict: dict

    def __init__(self, body_dict: dict) -> None:
        self.__body_dict = body_dict

    @property
    def aggs(self) -> dict:
        """
        The optional aggregations dict.
        """
        body_dict = self.__body_dict.get('aggs')
        if body_dict is None:
            raise BadPostJsonError(
                'aggs',
                message='"aggs" must be given'
            )
        return body_dict
