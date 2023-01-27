# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

class DataSource(object):

    def __init__(self, config):
        for k, v in config.items():
            setattr(self, k, v)
