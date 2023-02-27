# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List

from .datasource_error import DataSourceError


class DataSource(object):

    def __init__(self, config: Dict, expected: List = []):
        for k in expected:
            if k not in config:
                raise DataSourceError(title='Incorrect configuration',
                                      detail=f'{k} missing in config dict')
        for k, v in config.items():
            setattr(self, k, v)
