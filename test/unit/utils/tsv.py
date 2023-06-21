# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest import (TestCase)

from tol.utils import convert_csv_to_json


class TestTSV(TestCase):
    def test_convert_tsv_to_json(self):
        expected = [
            {
                'order': 'Sapindales',
                'family': 'Sapindaceae',
                'genus': 'Acer',
                'species': 'acuminatum'
            },
            {
                'order': 'Sapindales',
                'family': 'Sapindaceae',
                'genus': None,
                'species': 'albopurpurascens'
            }
        ]

        dir_name = os.path.dirname(__file__)
        file = open(f'{dir_name}/test.tsv', 'rb')
        json = convert_csv_to_json(file, '\t')
        self.assertEqual(expected, json)
