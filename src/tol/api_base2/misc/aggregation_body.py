# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

from ..exception import BadPostJsonError


class AggregationBody:
    """
    Parses the parameters from a query string for a Aggregation POST
    endpoint.
    """

    def __init__(self, body_dict: Dict) -> None:
        self.__body_dict = body_dict

    @property
    def aggregations(self) -> Dict:
        """
        The optional aggregations dict.
        """
        body_dict = self.__body_dict.get('aggregations')
        if body_dict is None:
            raise BadPostJsonError(
                'aggregations',
                message='"aggregations" must be given'
            )
        return body_dict
