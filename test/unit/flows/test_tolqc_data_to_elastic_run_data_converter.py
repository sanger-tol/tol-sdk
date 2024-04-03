# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    TolqcDataToElasticRunDataConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['data', 'run', 'sample', 'platform', 'species', 'specimen',
                'accession', 'library', 'library_type']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_data = RelationshipConfig()
        rc_data.to_one = {
            'run': 'run',
            'sample': 'sample',
            'library': 'library'
        }
        rc_run = RelationshipConfig()
        rc_run.to_one = {
            'platform': 'platform'
        }

        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'specimen': 'specimen'
        }

        rc_specimen = RelationshipConfig()
        rc_specimen.to_one = {
            'accession': 'accession',
            'species': 'species'
        }

        rc_library = RelationshipConfig()
        rc_library.to_one = {
            'library_type': 'library_type'
        }

        return {'data': rc_data,
                'run': rc_run,
                'sample': rc_sample,
                'specimen': rc_specimen,
                'library': rc_library}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        # with data.run relationship
        if source.id == 'data2_id' and relationship_name == 'run':
            return source._host.data_object_factory(
                id_='run2_id',
                type_='run',
                attributes={'start': 'time1'}
            )

        # with data.run.platform nested relationship
        if source.id == 'run2_id' and relationship_name == 'platform':
            return source._host.data_object_factory(
                id_='platform1_id',
                type_='platform',
                attributes={'model': 'model1'}
            )

        # with data.sample relationship
        if source.id == 'data4_id' and relationship_name == 'sample':
            return source._host.data_object_factory(
                id_='sample1_id',
                type_='sample',
                attributes={}
            )

        # with data.sample.specimen nested relationship
        if source.id == 'data5_id' and relationship_name == 'sample':
            return source._host.data_object_factory(
                id_='sample2_id',
                type_='sample',
                attributes={}
            )

        if source.id == 'sample2_id' and relationship_name == 'specimen':
            return source._host.data_object_factory(
                id_='specimen1_id',
                type_='specimen',
                attributes={}
            )

        # with data.sample.specimen.accession nested relationship
        if source.id == 'specimen2_id' and relationship_name == 'accession':
            return source._host.data_object_factory(
                id_='accession1_id',
                type_='accession',
                attributes={}
            )

        if source.id == 'sample3_id' and relationship_name == 'specimen':
            return source._host.data_object_factory(
                id_='specimen2_id',
                type_='specimen',
                attributes={'supplied name': 'supplied_name1'}
            )

        # with data.sample.specimen.species nested relationship
        if source.id == 'specimen3_id' and relationship_name == 'species':
            return source._host.data_object_factory(
                id_='species1_id',
                type_='species',
                attributes={'taxon_id': 'taxon_id1'}
            )

        if source.id == 'sample4_id' and relationship_name == 'specimen':
            return source._host.data_object_factory(
                id_='specimen3_id',
                type_='specimen',
                attributes={}
            )
        if relationship_name == 'library':
            return source._host.data_object_factory(
                id_='library_id',
                type_='library',
                attributes={}
            )
        if relationship_name == 'library_type':
            return source._host.data_object_factory(
                id_='library_type_id',
                type_='library_type',
                attributes={
                    'reporting_category': 'rnaseq'
                }
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['run_data']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTolqcDataToElasticRunDataConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolqcDataToElasticRunDataConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806

        # with no relationships
        obj1 = CoreDataObject(
            id_='data1_id',
            type_='data',
            attributes={'name_root': 'id1',
                        'tag_index': 'data1_tag_index',
                        'lims_qc': 'data1_manual_qc'}
        )

        # with data.run relationship
        run1 = CoreDataObject(
            id_='run1_id',
            type_='run',
            attributes={'start': 'time1'}
        )

        obj2 = CoreDataObject(
            id_='data2_id',
            type_='data',
            attributes={'tag_index': 'data2_tag_index',
                        'lims_qc': 'data2_manual_qc'},
            to_one={'run': run1}
        )

        # with data.run.platform nested relationship
        platform1 = CoreDataObject(
            id_='platform1_id',
            type_='platform',
            attributes={'model': 'model1'}
        )

        run2 = CoreDataObject(
            id_='run2_id',
            type_='run',
            attributes={},
            to_one={'platform': platform1}
        )

        obj3 = CoreDataObject(
            id_='data3_id',
            type_='data',
            attributes={'tag_index': 'data3_tag_index',
                        'lims_qc': 'data3_manual_qc'},
            to_one={'run': run2}
        )

        # with data.sample relationship
        sample1 = CoreDataObject(
            id_='sample1_id',
            type_='sample',
            attributes={}
        )

        obj4 = CoreDataObject(
            id_='data4_id',
            type_='data',
            attributes={'tag_index': 'data4_tag_index',
                        'lims_qc': 'data4_manual_qc'},
            to_one={'sample': sample1}
        )

        # with data.sample.specimen nested relationship
        specimen1 = CoreDataObject(
            id_='specimen1_id',
            type_='specimen',
            attributes={}
        )

        sample2 = CoreDataObject(
            id_='sample2_id',
            type_='sample',
            attributes={},
            to_one={'specimen': specimen1}
        )

        obj5 = CoreDataObject(
            id_='data5_id',
            type_='data',
            attributes={'tag_index': 'data5_tag_index',
                        'lims_qc': 'data5_manual_qc'},
            to_one={'sample': sample2}
        )

        # with data.sample.specimen.accession nested relationship
        accession1 = CoreDataObject(
            id_='accession1_id',
            type_='accession',
            attributes={}
        )

        specimen2 = CoreDataObject(
            id_='specimen2_id',
            type_='specimen',
            attributes={},
            to_one={'accession': accession1}
        )

        sample3 = CoreDataObject(
            id_='sample3_id',
            type_='sample',
            attributes={},
            to_one={'specimen': specimen2}
        )

        obj6 = CoreDataObject(
            id_='data6_id',
            type_='data',
            attributes={'tag_index': 'data6_tag_index',
                        'lims_qc': 'data6_manual_qc'},
            to_one={'sample': sample3}
        )

        # with data.sample.specimen.species nested relationship
        species1 = CoreDataObject(
            id_='species1_id',
            type_='species',
            attributes={'taxon_id': 'taxon_id1'}
        )

        specimen3 = CoreDataObject(
            id_='specimen3_id',
            type_='specimen',
            attributes={},
            to_one={'species': species1}
        )

        sample4 = CoreDataObject(
            id_='sample4_id',
            type_='sample',
            attributes={},
            to_one={'specimen': specimen3}
        )

        obj7 = CoreDataObject(
            id_='data7_id',
            type_='data',
            attributes={'tag_index': 'data7_tag_index',
                        'lims_qc': 'data7_manual_qc'},
            to_one={'sample': sample4}
        )

        # testing
        # with no relationships
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        print(f'the returned data object is {ret1.attributes}')
        self.assertEqual('id1', ret1.id)
        self.assertEqual('run_data', ret1.type)
        self.assertEqual(ret1.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data1_tag_index',
            'manual_qc': 'data1_manual_qc',
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.run relationship
        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual('run_data', ret2.type)
        self.assertEqual(ret2.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data2_tag_index',
            'manual_qc': 'data2_manual_qc',
            'run_start': 'time1',
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None,
            'run': 'run1_id',
            'position': None,
            'run_complete': None
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.run.platform relationship
        converteds = converter.convert(obj3)
        ret3 = next(converteds)
        self.assertEqual('run_data', ret3.type)
        self.assertEqual(ret3.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data3_tag_index',
            'manual_qc': 'data3_manual_qc',
            'instrument_model': 'model1',
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None,
            'run': 'run2_id',
            'position': None,
            'run_start': None,
            'run_complete': None
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.sample relationship
        converteds = converter.convert(obj4)
        ret4 = next(converteds)
        self.assertEqual('run_data', ret4.type)
        self.assertEqual(ret4.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data4_tag_index',
            'manual_qc': 'data4_manual_qc',
            'sequencing_request': {'id': 'sample1_id'},
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None,
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.sample.specimen relationship
        converteds = converter.convert(obj5)
        ret5 = next(converteds)
        self.assertEqual('run_data', ret5.type)
        self.assertEqual(ret5.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data5_tag_index',
            'manual_qc': 'data5_manual_qc',
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None,
            'tolid': {'id': 'specimen1_id'},
            'specimen': {'id': None},
            'sequencing_request': {'id': 'sample2_id'}
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.sample.specimen.accession relationship
        converteds = converter.convert(obj6)
        ret6 = next(converteds)
        self.assertEqual('run_data', ret6.type)
        self.assertEqual(ret6.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data6_tag_index',
            'manual_qc': 'data6_manual_qc',
            'auto_qc': None,
            'qc': None,
            'tag_sequence': None,
            'tag2_sequence': None,
            'sequencing_request': {'id': 'sample3_id'},
            'biospecimen_id': 'accession1_id',
            'tolid': {'id': 'specimen2_id'},
            'specimen': {'id': None},
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with data.sample.specimen.species relationship
        converteds = converter.convert(obj7)
        ret7 = next(converteds)
        self.assertEqual('run_data', ret7.type)
        self.assertEqual(ret7.attributes, {
            'reporting_category': 'rnaseq',
            'tag_index': 'data7_tag_index',
            'manual_qc': 'data7_manual_qc',
            'auto_qc': None,
            'qc': None,
            'sequencing_request': {'id': 'sample4_id'},
            'tag_sequence': None,
            'tag2_sequence': None,
            'auto_qc': None,
            'qc': None,
            'tolid': {'id': 'specimen3_id'},
            'specimen': {'id': None},
            'species': {'id': 'taxon_id1'}
        })
