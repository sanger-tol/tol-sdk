# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional

import requests

from .converter import LabwhereApiTransfer


class LabwhereApiClient:
    """
    Takes LabWhere API transfers and connects to a remote
    LabWhere API.
    """

    def __init__(
        self,
        labwhere_url: str,
    ) -> None:
        self.__labwhere_url = labwhere_url

    def get_detail(
        self,
        object_type: str,
        object_id: str
    ) -> Optional[LabwhereApiTransfer]:
        """
        Gets a single Labwhere API transfer for the object of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url = self.__detail_url(object_type, object_id)
        return self.__fetch_detail(url)

    def __fetch_detail(
        self,
        url: str
    ) -> Optional[LabwhereApiTransfer]:

        r = requests.get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def __detail_url(self, object_type: str, object_id: str) -> str:
        return f'{self.__labwhere_url}/{object_type}s/{object_id}'
