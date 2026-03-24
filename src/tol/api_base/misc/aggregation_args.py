# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from werkzeug.datastructures import MultiDict


class AggregationArgs:
    """
    Parses the arguments for an Aggregation POST endpoint.
    These could come from the query string (request_args) or the POST body (body_dict).
    """

    __slots__ = ['__args_dict']
    __args_dict: dict

    def __init__(
        self,
        body_json: Any | None,
        request_args: MultiDict | None = None
    ) -> None:
        # The accepted JSON body is an object (Python dict). It cannot be a list
        assert isinstance(body_json, dict)

        self.__args_dict = (
            (body_json if body_json else {})
            | (request_args.to_dict() if request_args else {})
        )
