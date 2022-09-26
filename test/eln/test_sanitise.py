# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import
from tol.eln import sanitise_value
from unittest import TestCase


class TestSanitise(TestCase):

    def test_sanitise_value(self):
        self.assertEqual("field", sanitise_value("field"))
        self.assertEqual("field", sanitise_value("field "))
        self.assertEqual("field", sanitise_value("field \n"))
        self.assertEqual("field", sanitise_value("field \\n"))
        self.assertEqual("field", sanitise_value("\n field "))
        self.assertEqual("field", sanitise_value("\\n field "))
        self.assertEqual("field", sanitise_value("\t field\t "))
        self.assertEqual("field", sanitise_value("\\t field\\t "))
