# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime
from unittest import (TestCase)

from tol.excel import convert_excel_to_json


class TestExcel(TestCase):
    def test_convert_excel_to_json(self):
        expected = [{'heading1': 'cell1',
                    'heading2': 'cell2'},
                    {'heading1': 'cell3',
                    'heading2': 'cell4'},
                    {'heading1': datetime(year=2023, month=1, day=1),
                    'heading2': datetime(year=2023, month=1, day=1)}]
        dir_name = os.path.dirname(__file__)
        file = open(f'{dir_name}/test.xlsx', 'rb')
        json = convert_excel_to_json(file, 'Sheet1')
        self.assertEqual(expected, json)
