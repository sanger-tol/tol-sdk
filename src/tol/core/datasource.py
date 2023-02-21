# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict


class DataSource(object):

    def __init__(self, config: Dict):
        for k, v in config.items():
            setattr(self, k, v)
