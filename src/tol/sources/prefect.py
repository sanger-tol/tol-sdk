# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import typing

from ..core import (
    core_data_object
)

if typing.TYPE_CHECKING:
    from ..prefect import PrefectDataSource


def prefect(
    insecure: bool = False,
    **kwargs
) -> PrefectDataSource:
    """
    Note - this must be the main entrypoint to the prefect SDK.

    Do not import anything from the `prefect` namespace before running
    this function.
    """

    api_url = os.environ['PREFECT_URL'] + os.environ['PREFECT_API_PATH']

    # this must be set before importing anything from prefect. failure
    # to do so causes the prefect SDK to spin up a local instance.
    os.environ['PREFECT_API_URL'] = api_url

    if insecure:
        os.environ['PREFECT_API_TLS_INSECURE_SKIP_VERIFY'] = '1'

    from ..prefect import create_prefect_datasource

    prefect = create_prefect_datasource(
        api_url,
        insecure=insecure
    )
    core_data_object(prefect)

    return prefect
