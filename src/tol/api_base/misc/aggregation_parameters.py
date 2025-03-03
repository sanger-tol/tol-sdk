# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Optional

from .filter_utils import FilterUtils


class AggregationParameters:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    def __init__(self, request_args: Dict[str, str]) -> None:
        self.__request_args = request_args

    @property
    def filter(self) -> Optional[str]:  # noqa A003
        """
        The optional filter JSON string.
        """
        filter_string = self.__request_args.get('filter')
        if filter_string is None:
            return None

        return FilterUtils.parse_to_datasource_filter('filter', filter_string)
