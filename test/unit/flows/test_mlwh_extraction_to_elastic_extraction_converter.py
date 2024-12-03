# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    MlwhExtractionToElasticExtractionConverter
)


class _MockDataSourceRelational(DataSource):

    @property
    def supported_types(self):
        return ['extraction']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['long_read_qc_result']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestMlwhExtractionToElasticExtractionConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = MlwhExtractionToElasticExtractionConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='Test1',
            type_='long_read_qc_result',
            attributes={
                'assay_type': 'assay1',
                'units': 'units1',
                'value': 'value1',
                'recorded_at': 'recorded1',
                'sample_id': 'sample1',
                'labware_barcode': 'barcode1',
                'qc_status': 'qc1',
                'qc_status_decision_by': 'decision1'

            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('sample1', ret1.id)
        self.assertEqual('extraction', ret1.type)
        self.assertEqual(ret1.attributes, {
            'assay1_units': 'units1',
            'assay1_value': 'value1',
            'assay1_recorded_at': 'recorded1',
            'tissue_prep_fluidx_id': 'barcode1',
            'qc_status': 'qc1',
            'qc_status_decision_by': 'decision1'

        })

        with self.assertRaises(StopIteration):
            next(converteds)

        obj2 = CoreDataObject(
            id_='Test2',
            type_='long_read_qc_result',
            attributes={
                'assay_type': 'assay2',
                'units': 'units2',
                'value': '17.235',
                'recorded_at': 'recorded2',
                'sample_id': 'sample2',
                'labware_barcode': 'barcode2',
                'qc_status': 'qc2',
                'qc_status_decision_by': 'decision2'
            }
        )
        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual('sample2', ret2.id)
        self.assertEqual('extraction', ret2.type)
        self.assertEqual(ret2.attributes, {
            'assay2_units': 'units2',
            'assay2_value': 17.235,
            'assay2_recorded_at': 'recorded2',
            'tissue_prep_fluidx_id': 'barcode2',
            'qc_status': 'qc2',
            'qc_status_decision_by': 'decision2'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
