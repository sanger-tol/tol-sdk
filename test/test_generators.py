# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import
from tol.eln import generate_flattened_type
from unittest import TestCase


class MockList():
    def list(self):
        return [[1, 2, 3], [4, 5, 6]]


class TestGenerators(TestCase):

    def test_generate_flattened_type(self):
        mocklist = MockList()
        expected = [1, 2, 3, 4, 5, 6]
        response = list(generate_flattened_type(mocklist))
        self.assertEqual(expected, response)
