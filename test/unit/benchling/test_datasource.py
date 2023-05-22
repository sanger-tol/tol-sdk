# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest import TestCase

from tol.benchling.datasource import BenchlingDataSource


class TestBenchlingDataSource(TestCase):
    def test_instantiation(self):
        import logging
        logging.error(os.environ)
        #ds.get_by_id('test', [])
