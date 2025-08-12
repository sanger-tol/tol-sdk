# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime
from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.excel import convert_excel_to_json


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample', 'specimen']

    @property
    def attribute_types(self):
        return {}


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'specimen']

    @property
    def attribute_types(self):
        return {}

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'specimen': 'specimen'
        }
        return {'sample': rc_sample}

    def get_to_one_relation(self, source: DataObject, relationship_name: str):
        print(f'Called with {source.id} {relationship_name}')
        if source.id == 'sample_id3':
            return source._host.data_object_factory(
                id_='specimen_id3',
                type_='specimen',
                attributes={'name': 'specimen_name1'}
            )

        if source.id == 'sample_id4':
            return source._host.data_object_factory(
                id_='specimen_id4',
                type_='specimen',
                attributes={'name': 'specimen_name2'}
            )

    def get_to_many_relations(self):
        raise NotImplementedError()


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
