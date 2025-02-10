# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import json
from functools import cache
from io import BytesIO

from minio import Minio

from . import JsonDataSource
from ..core import (
    DataSource,
    DataSourceError,
)


class S3JsonDataSource(
    JsonDataSource
):
    """
    A subclass of JsonDataSource that loads JSON data directly from an S3 bucket.
    """

    def __init__(
        self,
        config: dict,
        s3_endpoint: str,
        s3_access_key: str,
        s3_secret_key: str,
        s3_bucket: str,
        s3_object: str,
        secure: bool = True
    ) -> None:
        DataSource.__init__(self, config=config)

        # Initialize MinIO client
        self.minio_client = Minio(
            s3_endpoint,
            access_key=s3_access_key,
            secret_key=s3_secret_key,
            secure=secure
        )

        self.config = config
        self.id_attribute = config.get('id_attribute')

        # Load JSON data from S3
        raw_data = self._load_json_from_s3(s3_bucket, s3_object)

        # Set raw data
        self._raw_data = raw_data
        self._keyed_by_id = {
            v[self.id_attribute]: v
            for v in self._raw_data
            if self.id_attribute in v
        }

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            self.type: {
                k: v['type']
                for k, v in self.mappings.items()
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def _load_json_from_s3(self, bucket: str, object_name: str):
        """Fetch and load JSON data from an S3 bucket."""
        try:
            response = self.minio_client.get_object(bucket, object_name)
            json_data = json.load(BytesIO(response.read()))  # Read and parse JSON
            return json_data
        except Exception as e:
            raise DataSourceError(f'Failed to load JSON from S3: {e}')
