# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from ...api_client.exception import BadQueryArgError
from ...core import DataSourceFilter


class FilterUtils:
    @classmethod
    def parse_to_datasource_filter(cls, __key: str, __value: str) -> DataSourceFilter:
        try:
            filter_dict = json.loads(__value)
            if isinstance(filter_dict, dict):
                dsf = DataSourceFilter(**filter_dict)
                return dsf
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be valid JSON'
            )
        except json.JSONDecodeError:
            raise BadQueryArgError(
                __key,
                __value,
                message=f'The {__key} must be valid JSON'
            )
