# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..core import (
    core_data_object
)
from ..open_citations import (
    OpenCitationsDataSource,
    create_open_citations_datasource,
)


def _compose_open_citations_url(base_url: str, api_path: str) -> str:
    base_url = base_url.rstrip('/')
    api_path = f'/{api_path.strip("/")}' if api_path else ''
    if api_path and base_url.endswith(api_path):
        return base_url
    return f'{base_url}{api_path}'


def open_citations(**kwargs) -> OpenCitationsDataSource:
    open_citations_url = _compose_open_citations_url(
        os.getenv(
            'OPEN_CITATIONS_URL',
            Defaults.OPEN_CITATIONS_URL,
        ),
        os.getenv(
            'OPEN_CITATIONS_API_PATH',
            Defaults.OPEN_CITATIONS_API_PATH,
        ),
    )

    open_citations_ds = create_open_citations_datasource(
        open_citations_url=open_citations_url,
        access_token=os.getenv('OPEN_CITATIONS_ACCESS_TOKEN'),
    )
    core_data_object(open_citations_ds)
    return open_citations_ds
