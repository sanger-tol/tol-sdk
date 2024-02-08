# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import (Dict, Iterable, List)

import requests

from ..core import (
    DataObject,
    DataSource,
    DataSourceError
)
from ..core.operator import (
    Upserter
)


class StsDataSource(DataSource, Upserter):
    """
    This is a very simple DataSource that provides access to certain writeable
    endpoints in STS via the standard DataSource methods (upsert, etc.)
    There is also direct access to any endpoint via the native_***() methods
    """

    def __init__(self, config: Dict):
        super().__init__(config, expected=['url', 'key'])

    @property
    def supported_types(self) -> List[str]:
        return ['sequencing_request', 'extraction']

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'sequencing_request': {
                'platform': 'str',
                'fluidx_id': 'str',
                'submission_date': 'datetime'
            },
            'extraction': {
                'sample_id': 'str',
                'fluidx_id': 'str',
                'extraction_type': 'str',
                'extraction_date': 'datetime'
            }
        }

    def _encode_date(self, d):
        return d.strftime('%Y-%m-%d %H:%M:%S')

    def __post_sequencing_requests(self, sequencing_requests: Iterable[DataObject]):
        """
        We are expecting a list of DataObjects with:
        id
        platform
        fluidx_id
        submission_date
        """
        for sr in sequencing_requests:
            payload = {'platform': sr.platform,
                       'fluidx_id': sr.fluidx_id,
                       'sample_ref': sr.id,
                       'submit_date': self._encode_date(sr.submission_date)}
            r = self.native_post(
                '/sequencing-requests',
                json=payload
            )
            if r.ok:
                print(f'OK: {sr.id}')
            else:
                print(
                    f'A sample failed with code {r.status_code}, '
                    f'and response {r.json()}, '
                    f'containing data: {payload}'
                )

    def __post_extractions(self, extractions: Iterable[DataObject]):
        """
        We are expecting a list of DataObjects with:
        id (the ELN id)
        fluidx_id
        sample_id
        extraction_type (uppercase)
        extraction_date
        """
        for extraction in extractions:
            payload = {'eln_id': extraction.id,
                       'sample_id': extraction.sample_id,
                       'fluidx_id': extraction.fluidx_id,
                       'type': extraction.extraction_type,
                       'extraction_date': self._encode_date(extraction.extraction_date)}
            r = self.native_post(
                f'/ep_samples/{extraction.fluidx_id}',
                json=payload
            )
            if r.ok:
                print(f'OK: {extraction.id}')
            else:
                print(
                    f'A sample failed with code {r.status_code}, '
                    f'and response {r.json()}, '
                    f'containing data: {payload}'
                )

    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject]
    ) -> None:
        if object_type == 'sequencing_request':
            self.__post_sequencing_requests(objects)
        elif object_type == 'extraction':
            self.__post_extractions(objects)
        else:
            raise DataSourceError('Only objects of type sequencing_request and extraction '
                                  'are handled by StsDataSource')

    # Everything below here is to do with allowing native endpoint requests

    def __override_method(self, method, relative_url, headers=None, **kwargs):
        if headers is None:
            new_headers = {
                'Authorization': self.key
            }
        else:
            new_headers = {
                'Authorization': self.key,
                **headers
            }
        return method(
            f'{self.url}/{relative_url}',
            headers=new_headers,
            **kwargs
        )

    def native_get(self, relative_url, **kwargs):
        return self.__override_method(
            requests.get,
            relative_url,
            **kwargs
        )

    def native_post(self, relative_url, **kwargs):
        return self.__override_method(
            requests.post,
            relative_url,
            **kwargs
        )

    def native_put(self, relative_url, **kwargs):
        return self.__override_method(
            requests.put,
            relative_url,
            **kwargs
        )

    def native_patch(self, relative_url, **kwargs):
        return self.__override_method(
            requests.patch,
            relative_url,
            **kwargs
        )

    def native_delete(self, relative_url, **kwargs):
        return self.__override_method(
            requests.delete,
            relative_url,
            **kwargs
        )
