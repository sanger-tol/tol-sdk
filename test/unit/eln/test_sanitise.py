# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from unittest import TestCase

from tol.eln import sanitise_value


class TestSanitise(TestCase):

    def test_sanitise_value(self):
        self.assertEqual('', sanitise_value(None))
        self.assertEqual('default', sanitise_value(None, default='default'))
        self.assertIsNone(sanitise_value(None, default=None))
        self.assertIsNone(sanitise_value('', default=None))
        self.assertEqual('field', sanitise_value('field', default='default'))
        self.assertEqual('field', sanitise_value('field'))
        self.assertEqual('field', sanitise_value('field '))
        self.assertEqual('field', sanitise_value('field \n'))
        self.assertEqual('field', sanitise_value('field \\n'))
        self.assertEqual('field', sanitise_value('\n field '))
        self.assertEqual('field', sanitise_value('\\n field '))
        self.assertEqual('field', sanitise_value('\t field\t '))
        self.assertEqual('field', sanitise_value('\\t field\\t '))

        self.assertEqual(0, sanitise_value(0))
        self.assertEqual(0, sanitise_value(None, 0))
