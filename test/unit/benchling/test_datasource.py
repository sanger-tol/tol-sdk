# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.benchling.datasource import BenchlingDataSource


class TestBenchlingDataSource(TestCase):
    def test_instantiation(self):
        BenchlingDataSource({})
