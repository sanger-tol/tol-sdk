# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Optional

from ..exception import BadQueryArgError


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
    def page_number(self) -> Optional[int]:
        """
        The optional number of the page of results.
        """
        page_number = self.__request_args.get('page_number')
        if page_number is None:
            return None

        return self.__parse_to_positive_int('page_number', page_number)

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
