# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import io
import os
from datetime import datetime
from unittest import (TestCase)

import pandas as pd

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.excel import convert_data_objects_to_excel, convert_excel_to_json


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()

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

    def test_convert_data_objects_to_excel(self):
        CoreDataObject = core_data_object(_MockDataSource(config={}))  # noqa N806
        CoreDataObject = core_data_object(_MockDataSourceRelational(config={}))  # noqa N806

        obj1 = CoreDataObject(
            id_='sample_id1',
            type_='sample',
            attributes={'column1': 'value1',
                        'column2': 'value2'}
        )
        obj2 = CoreDataObject(
            id_='sample_id2',
            type_='sample',
            attributes={'column1': 'value3',
                        'column2': 'value4'}
        )

        specimen1 = CoreDataObject(
            id_='specimen_id3',
            type_='specimen',
            attributes={'name': 'specimen_name1'}
        )

        specimen2 = CoreDataObject(
            id_='specimen_id4',
            type_='specimen',
            attributes={'name': 'specimen_name2'}
        )

        obj3 = CoreDataObject(
            id_='sample_id3',
            type_='sample',
            attributes={'column1': 'value5',
                        'column2': 'value6'},
            to_one={'specimen': specimen1}
        )

        obj4 = CoreDataObject(
            id_='sample_id4',
            type_='sample',
            attributes={'column1': 'value7',
                        'column2': 'value8'},
            to_one={'specimen': specimen2}
        )

        specimen3 = CoreDataObject(
            id_='specimen_id5',
            type_='specimen',
            attributes={}
        )

        specimen4 = CoreDataObject(
            id_='specimen_id6',
            type_='specimen',
            attributes={}
        )

        obj5 = CoreDataObject(
            id_='sample_id5',
            type_='sample',
            attributes={'column1': 'value9',
                        'column2': 'value10'},
            to_one={'specimen': specimen3}
        )

        obj6 = CoreDataObject(
            id_='sample_id6',
            type_='sample',
            attributes={'column1': 'value11',
                        'column2': 'value12'},
            to_one={'specimen': specimen4}
        )

        mock_objects1 = [obj1, obj2]  # no to_one relationships
        mock_objects2 = [obj3, obj4]  # to_one_relationship with existing relationship attribute
        mock_objects3 = [obj5, obj6]  # to_one_relationship with no relationship attribute

        body1 = [{'display_name': 'Column 1', 'hidden': False, 'key': 'column1'},
                 {'display_name': 'Column 2', 'hidden': False, 'key': 'column2'}]

        body2 = [{'display_name': 'Specimen Name', 'hidden': False, 'key': 'specimen.name'},
                 {'display_name': 'Column 2', 'hidden': False, 'key': 'column2'}]

        body3 = [{'display_name': 'Specimen Name', 'hidden': False, 'key': 'specimen.name'},
                 {'display_name': 'Column 2', 'hidden': False, 'key': 'column2'}]

        expected1 = pd.DataFrame([
            {'Column 1': 'value1', 'Column 2': 'value2'},
            {'Column 1': 'value3', 'Column 2': 'value4'}
        ])

        expected2 = pd.DataFrame([
            {'Specimen Name': 'specimen_name1', 'Column 2': 'value6'},
            {'Specimen Name': 'specimen_name2', 'Column 2': 'value8'}
        ])

        expected3 = pd.DataFrame([
            {'Specimen Name': None, 'Column 2': 'value10'},
            {'Specimen Name': None, 'Column 2': 'value12'}
        ])

        # with no relationships
        output_stream = convert_data_objects_to_excel(mock_objects1, body1, 'Sheet1')
        output_data = pd.read_excel(io.BytesIO(output_stream.getvalue()), sheet_name='Sheet1')
        pd.testing.assert_frame_equal(expected1, output_data)

        # with to_one_relationship with existing relationship attribute
        output_stream = convert_data_objects_to_excel(mock_objects2, body2, 'Sheet1')
        output_data = pd.read_excel(io.BytesIO(output_stream.getvalue()), sheet_name='Sheet1')
        pd.testing.assert_frame_equal(expected2, output_data)

        # with to_one_relationship with None relationship attribute
        output_stream = convert_data_objects_to_excel(mock_objects3, body3, 'Sheet1')
        output_data = pd.read_excel(io.BytesIO(output_stream.getvalue()), sheet_name='Sheet1')
        pd.testing.assert_frame_equal(expected3, output_data, check_dtype=False)
