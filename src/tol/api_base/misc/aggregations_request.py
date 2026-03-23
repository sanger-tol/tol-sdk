# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from werkzeug.datastructures import MultiDict


class AggregationParameters:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    __slots__ = ['__request_args']
    __request_args: dict

    def __init__(self, request_args: MultiDict) -> None:
        self.__request_args = request_args.to_dict()


class AggregationBody:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    __slots__ = ['__body_dict']
    __body_dict: dict

    def __init__(self, body_dict: MultiDict) -> None:
        self.__body_dict = body_dict.to_dict()
