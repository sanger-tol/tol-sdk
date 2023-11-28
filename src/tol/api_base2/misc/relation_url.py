# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...core import DataSourceError


class RelataionshipHopsParser:
    """
    Parses the relationship hops from a related URL.
    """

    def __init__(self, url_suffix: str) -> None:
        self.__suffix = url_suffix

    @property
    def relationship_hops(self) -> list[str]:
        hops = self.__suffix.split('/')
        self.__validate_all_hops(hops)
        return hops

    def __validate_all_hops(self, hops: list[str]) -> None:
        for hop in hops:
            self.__validate_hop(hop)

    def __validate_hop(self, hop: str) -> None:
        if not self.__hop_is_valid(hop):
            detail = (
                'The given recursive relationship '
                'path is invalid. Please check the '
                'provided information, and try again.'
            )
            raise DataSourceError(
                title='Invalid Relationship',
                detail=detail,
                status_code=400
            )

    def __hop_is_valid(self, hop: str) -> None:
        return hop and not hop.isspace()
