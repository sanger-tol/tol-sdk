# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tempfile import NamedTemporaryFile
from typing import Any, Protocol

import gdown

from .csv_datasource import CsvDataSource


class GoogleFetcher(Protocol):
    def __call__(
        self,
        google_file_id: str,
        local_filename: str,
    ) -> None:
        ...


def fetch_from_google_drive(
    google_file_id: str,
    local_filename: str,
) -> None:
    gdown.download(id=google_file_id, output=local_filename)


def google_csv_datasource_factory(
    *,
    google_file_id: str,
    google_fetcher: GoogleFetcher = fetch_from_google_drive,
    **kwargs: Any,
) -> CsvDataSource:

    with NamedTemporaryFile() as temp_fil:
        filename = temp_fil.name

        google_fetcher(google_file_id, filename)

        return CsvDataSource(
            filename,
            **kwargs,
        )
