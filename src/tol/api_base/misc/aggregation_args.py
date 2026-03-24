# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from werkzeug.datastructures import MultiDict

from ...api_client.exception import BadPostJsonError


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
        # Validate JSON body: must exist, and should be an object (not a list)
        # The accepted JSON body is an object (Python dict). It cannot be a list
        if not isinstance(body_json, dict):
            raise TypeError("JSON body must be an object")

        self.__args_dict = (
            (body_json if body_json else {})
            | (request_args.to_dict() if request_args else {})
        )
