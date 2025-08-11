# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from tempfile import NamedTemporaryFile
from typing import Any, Protocol

from minio import Minio

from .excel_datasource import ExcelDataSource


class S3Fetcher(Protocol):
    def __call__(
        self,
        s3_filename: str,
        s3_bucket: str,
        local_filename: str,
    ) -> None:
        ...


def fetch_from_s3(
    s3_filename: str,
    s3_bucket: str,
    local_filename: str,
) -> None:

    s3_secure = os.getenv('S3_SECURE', 'true').lower() == 'true'

    minio_client = Minio(
        os.environ['S3_URI'],
        os.environ['S3_ACCESS_KEY'],
        secret_key=os.getenv('S3_SECRET_KEY'),
        secure=s3_secure,
    )

    minio_client.fget_object(s3_bucket, s3_filename, local_filename)


def s3_excel_datasource_factory(
    *,
    s3_filename: str,
    s3_bucket: str,
    sheetname: str,
    s3_fetcher: S3Fetcher = fetch_from_s3,
    **kwargs: Any,
) -> ExcelDataSource:

    with NamedTemporaryFile() as temp_fil:
        filename = temp_fil.name

        s3_fetcher(s3_filename, s3_bucket, filename)

        return ExcelDataSource(
            filename,
            sheetname,
            **kwargs,
        )
