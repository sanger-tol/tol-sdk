# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..google_sheets import (
    GoogleSheetDataSource
)
import json
import os


def googlesheet(googlesheet_id: str, mappings: dict = None, **kwargs) -> GoogleSheetDataSource:
    if mappings is None:
        mappings = {}

    gsds = GoogleSheetDataSource({
        'sheet_key': googlesheet_id,
        'mappings': mappings,
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        **kwargs
    })

    core_data_object(gsds)
    return gsds
