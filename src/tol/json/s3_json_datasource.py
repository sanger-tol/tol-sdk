# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import json
from io import BytesIO
from typing import Dict

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
        config: Dict,
        secure: bool = True
    ) -> None:
        DataSource.__init__(
            self,
            config=config,
            expected=[
                'uri',
                'type',
                'id_attribute',
                'mappings',
                's3_host',
                's3_access_key',
                's3_secret_key'
            ]
        )

        self.config = config
        self.id_attribute = config.get('id_attribute')

        self.bucket, self.object_name = self._extract_object_and_bucket(self.uri)

        # Initialize MinIO client
        self.minio_client = Minio(
            self.s3_host,
            access_key=self.s3_access_key,
            secret_key=self.s3_secret_key,
            secure=secure
        )

    def _load_json(self):
        """Fetch and load JSON data from an S3 bucket."""
        try:
            response = self.minio_client.get_object(self.bucket, self.object_name)
            json_data = json.load(BytesIO(response.read()))  # Read and parse JSON
            return json_data
        except Exception as e:
            raise DataSourceError(f'Failed to load JSON from S3: {e}')

    def _extract_object_and_bucket(self, uri: str):
        """Extract the bucket and object name from an S3 URI."""
        if uri.startswith('s3://'):
            uri = uri[5:]
        parts = uri.split('/')
        bucket = parts[0]
        object_name = '/'.join(parts[1:])
        return bucket, object_name
