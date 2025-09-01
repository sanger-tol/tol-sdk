# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import os
from typing import Iterable, Optional

from minio import Minio


class S3Client:

    def __init__(
        self,
        s3_uri: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: Optional[bool] = None,
    ):
        self.s3_uri = s3_uri or os.environ['S3_URI']
        self.access_key = access_key or os.environ['S3_ACCESS_KEY']
        self.secret_key = secret_key or os.environ['S3_SECRET_KEY']

        if secure is None:
            secure = os.getenv('S3_SECURE', 'true').lower() == 'true'

        self.client = Minio(
            self.s3_uri,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure
        )

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> None:

        self.client.fget_object(bucket_name, object_name, file_path)

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = None
    ) -> Iterable:
        yield from self.client.list_objects(bucket_name, prefix=prefix, recursive=True)

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> None:

        self.client.fput_object(bucket_name, object_name, file_path)
