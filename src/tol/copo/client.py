# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from itertools import chain
from typing import Optional

from .converter import CopoApiTransfer
from ..core import HttpClient


class CopoApiClient(HttpClient):
    """
    Takes COPO API transfers and connects to a remote
    COPO API.
    """

    def __init__(
        self,
        copo_url: str,
    ) -> None:
        super().__init__()
        self.__copo_url = copo_url

    def get_detail(
        self,
        object_type: str,
        object_ids: str
    ) -> Optional[CopoApiTransfer]:
        """
        Gets a single COPO API transfer for the object of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        urls = self.__detail_url(object_type, object_ids)
        return chain.from_iterable(
            self.__fetch_detail(url, object_type, id_)
            for id_, url in urls
        )

    def get_samples_in_manifest(
        self,
        manifest_id: str
    ) -> Optional[CopoApiTransfer]:
        """
        Gets a list of COPO API transfers for the samples in a
        specified manifest, or returns None if not found.
        """

        url = f'{self.__copo_url}/manifest/{manifest_id}'
        return self.__fetch_detail(
            url,
            'samples_in_manifest',  # A fudge to ignore the manifest-specific stuff
            manifest_id
        )

    def get_manifests(
        self,
        project: str,
        from_: datetime,
        to: datetime
    ) -> Optional[CopoApiTransfer]:
        """
        Gets a list of COPO API transfers for the samples in a
        specified manifest, or returns None if not found.
        """

        from_string = from_.isoformat()
        to_string = to.isoformat()
        url = f'{self.__copo_url}/manifest/{project}/{from_string}/{to_string}'
        manifest_ids = self.__fetch_detail(
            url,
            'manifests_between_dates'  # A fudge to ignore the manifest-specific stuff
        )
        return [
            {
                'tolsdk-type': 'manifest',
                'copo_id': id_
            }
            for id_ in manifest_ids
        ]

    def __fetch_detail(
        self,
        url: str,
        object_type: str,
        object_id: str = None
    ) -> Optional[CopoApiTransfer]:
        print(f'Getting {url}')
        session = self._get_session_with_retries()
        r = session.get(url, headers={'accept-encoding': 'gzip;q=0,deflate,sdch'})
        if r.status_code in [400, 404]:
            return [None]
        r.raise_for_status()
        if object_type == 'manifest':
            # The manifest does not exist if the response's data is
            # a list of strings
            if len(r.json()['data']) > 0 and isinstance(r.json()['data'][0], str):
                return [None]
            ret = [{'tolsdk-type': object_type, 'copo_id': object_id}]
        else:
            ret = r.json()['data']
        return ret

    def __detail_url(self, object_type: str, object_ids: str) -> str:
        # It is possible to request multiple sample IDs on the same request,
        # but if one of them is invalid, the request will return a 400 status code.
        # Therefore, we make a request for each sample ID.
        path = f'{object_type}'
        if object_type == 'sample':
            path = f'{object_type}/copo_id'
        return [
            (id_, f'{self.__copo_url}/{path}/{id_}')
            for id_ in object_ids
        ]
