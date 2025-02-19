# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional

from .filter_utils import FilterUtils


class StatsParameters:
    """
    Parses the parameters from a query string for a List GET
    endpoint.
    """

    def __init__(self, request_args: Dict[str, str]) -> None:
        self.__request_args = request_args

    @property
    def stats(self) -> Optional[int]:
        """The optional stats to return"""
        stats = self.__request_args.get('stats')
        if stats is None:
            return None

        return self._parse_to_list('stats', stats)

    @property
    def stats_fields(self) -> Optional[int]:
        """The optional stats to return"""
        stats_fields = self.__request_args.get('stats_fields')
        if stats_fields is None:
            return None

        return self._parse_to_list('stats_fields', stats_fields)

    @property
    def filter(self) -> Optional[str]:  # noqa A003
        """
        The optional filter JSON string.
        """
        filter_string = self.__request_args.get('filter')
        if filter_string is None:
            return None

        return FilterUtils.parse_to_datasource_filter('filter', filter_string)

    @property
    def _args(self) -> dict[str, Any]:
        return self.__request_args

    def _parse_to_list(self, __key: str, __value: str) -> int:
        return __value.split(',')


class GroupStatsParameters(StatsParameters):

    @property
    def group_by(self) -> list[str]:
        group_bys = self._args.get('group_by')
        if group_bys is None:
            return None

        return self._parse_to_list('group_by', group_bys)
