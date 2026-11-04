# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import (
    ApiDataSource,
    create_api_datasource
)
from ..core import (
    core_data_object
)


def api(
        url: str,
        api_path: str,
        api_data_path: str,
        dataspace: str,
        token: str = None,
        retries: int = 5,
        **kwargs
) -> ApiDataSource:
    ds = create_api_datasource(
        api_url=f'{url}{api_path}',
        token=token,
        data_prefix=f'{api_data_path}/{dataspace}' if dataspace else api_data_path,
        retries=retries
    )
    core_data_object(ds)
    return ds
