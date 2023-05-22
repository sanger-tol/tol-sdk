# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import re
from typing import Dict, Optional

from ..exception import BadQueryArgError
from ...core import DataSourceFilter


class ListGetParamaters:
    """
    Parses the parameters from a query string for a List GET
    endpoint.
    """

    def __init__(self, request_args: Dict[str, str]) -> None:
        self.__request_args = request_args

    @property
    def page_size(self) -> Optional[int]:
        """The optional page size to return"""
        page_size = self.__request_args.get('page_size')
        if page_size is None:
            return None

        return self.__parse_to_positive_int('page_size', page_size)

    @property
    def page(self) -> Optional[int]:
        """
        The optional number of the page of results.
        """
        page_number = self.__request_args.get('page')
        if page_number is None:
            return None

        return self.__parse_to_positive_int('page', page_number)

    @property
    def filter(self) -> Optional[str]:  # noqa A003
        """
        The optional filter JSON string.
        """
        filter_string = self.__request_args.get('filter')
        if filter_string is None:
            return None

        return self.__parse_to_datasource_filter('filter', filter_string)

    @property
    def sort_by(self) -> Optional[str]:
        """
        The optional column to sort by.
        """
        sort_by = self.__request_args.get('sort_by')
        if sort_by is None:
            return None

        return self.__parse_to_sort_by_string('sort_by', sort_by)

    def __parse_to_positive_int(self, __key: str, __value: str) -> int:
        self.__validate_is_digits(__key, __value)
        int_value = int(__value)
        if int_value < 1:
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be 1 or greater.'
            )
        return int_value

    def __validate_is_digits(self, __key: str, __value: str) -> None:
        if not __value.isdigit():
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be a positive integer.'
            )

    def __parse_to_sort_by_string(self, __key: str, __value: str) -> str:
        if not re.match(r'-?[a-z]', __value):
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be a column name, with or without leading -.'
            )
        return __value

    def __parse_to_datasource_filter(self, __key: str, __value: str) -> DataSourceFilter:
        try:
            filter_dict = json.loads(__value)
            dsf = DataSourceFilter()
            if type(filter_dict) is dict:
                if 'exact' in filter_dict:
                    dsf.exact = filter_dict['exact']
                if 'contains' in filter_dict:
                    dsf.contains = filter_dict['contains']
                if 'in_list' in filter_dict:
                    dsf.in_list = filter_dict['in_list']
                return dsf
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be valid JSON'
            )
        except json.JSONDecodeError:
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be valid JSON'
            )
