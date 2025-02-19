# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

from ...api_client.exception import BadPostJsonError


class AggregationBody:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    def __init__(self, body_dict: Dict) -> None:
        self.__body_dict = body_dict

    @property
    def aggs(self) -> Dict:
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
