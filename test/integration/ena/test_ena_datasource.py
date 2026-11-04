# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter
)
from tol.sources.ena import (
    ena
)


class TestEnaDataSource(TestCase):

    def test_attribute_types(self):
        eds = ena()

        assert 'taxon' in eds.attribute_types
        assert eds.attribute_types['taxon']['scientific_name'] == 'str'
        assert eds.attribute_types['assembly']['base_count'] == 'float'
        assert eds.attribute_types['sample']['collection_date'] == 'datetime'

    def test_get_by_id(self):
        eds = ena()

        ret = eds.get_by_id('sample', ['SAMEA111431194', 'SAMEA112819851'])
        obj1 = next(ret)
        obj2 = next(ret)

        self.assertEqual(obj1.id, 'SAMEA111431194')
        # Just pick out a few attributes to test
        self.assertEqual(obj1.collection_date, '2022-06-10')
        self.assertEqual(obj1.identified_by, 'MARKUS RUHSAM')
        self.assertEqual(obj2.type, 'sample')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_checklist(self):
        eds = ena()

        ret = eds.get_by_id('checklist', ['ERC000053', 'ERC000036'])
        obj1 = next(ret)
        obj2 = next(ret)

        self.assertEqual(obj1.id, 'ERC000053')
        # Just pick out a few attributes to test
        self.assertEqual(obj1.checklist.get('specimen_id'), [
            'optional',
            'free text',
            ''
        ])
        self.assertEqual(obj2.type, 'checklist')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_submittable_taxon(self):
        eds = ena()

        # Allow integer and string ids
        ret = eds.get_by_id('submittable_taxon', ['9606', '12345678', 9605, 'invalid_format'])
        obj1 = next(ret)
        obj2 = next(ret)
        obj3 = next(ret)
        obj4 = next(ret)
        self.assertEqual(obj1.id, '9606')
        # Just pick out a few attributes to test
        self.assertEqual(obj1.submittable, True)
        self.assertEqual(obj1.division, 'HUM')
        self.assertTrue(obj2 is None)
        self.assertEqual(obj3.id, '9605')
        # Just pick out a few attributes to test
        self.assertEqual(obj3.submittable, False)
        self.assertEqual(obj3.division, 'MAM')
        # Invalid format should return None
        self.assertIsNone(obj4)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        eds = ena()

        f = DataSourceFilter()
        f.and_ = {
            'scientific_name': {'in_list': {'value': ['Capra hircus', 'Mus musculus']}}
        }
        ret = list(eds.get_list('taxon', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '9925' in obj_ids
        assert '10090' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '9925':
                self.assertEqual(obj.id, '9925')
                # keeps flip-flopping between these two values at ENA
                self.assertIn(obj.common_name, ['domestic goat', 'goats'])
                self.assertEqual(obj.merged_tax_id, '57076')
            elif obj.id == '10090':
                self.assertEqual(obj.id, '10090')
                self.assertEqual(obj.genbank_common_name, 'house mouse')

    def test_get_list_page(self):
        eds = ena()

        f = DataSourceFilter()
        f.and_ = {
            'tax_eq': {'in_list': {'value': ['9662', '74645']}},
            'collection_date': {'lt': {'value': '2024-09-30'}}
        }
        ret, total = eds.get_list_page(
            'assembly',
            object_filters=f,
            page_number=1,
            page_size=4
        )

        assert total == 7
        self.assertEqual(len(ret), 4)
        obj1 = ret[0]
        self.assertEqual(obj1.id, 'GCA_054556025.1')
        self.assertEqual(obj1.collected_by, 'Quanshu Wu and Bingyao Huang') # noqa
        self.assertEqual(obj1.collection_date, '2022')

        obj2 = ret[1]
        self.assertEqual(obj2.id, 'GCA_054556105.1')

        obj3 = ret[2]
        self.assertEqual(obj3.id, 'GCA_922984935.1')

        obj4 = ret[3]
        self.assertEqual(obj4.id, 'GCA_922984935.2')
        self.assertEqual(obj4.sex, 'male')

    def test_relationship_config(self):
        eds = ena()

        self.assertEqual(eds.relationship_config['assembly'].to_one['study'], 'study')
        self.assertEqual(eds.relationship_config['assembly'].to_one['sample'], 'sample')
        self.assertEqual(eds.relationship_config['assembly'].to_one['taxon'], 'taxon')
        self.assertEqual(eds.relationship_config['assembly'].to_many['runs'], 'read_run')
        self.assertEqual(
            eds.relationship_config['read_run'].to_one['experiment'],
            'read_experiment'
        )
        self.assertEqual(eds.relationship_config['read_experiment'].to_many['runs'], 'read_run')

    def test_get_by_id_assembly(self):
        eds = ena()

        ret = eds.get_by_id('assembly', ['GCA_922984935.2'])
        assembly = next(ret)

        self.assertIsNotNone(assembly)
        self.assertEqual(assembly.type, 'assembly')
        self.assertEqual(assembly.id, 'GCA_922984935.2')
        self.assertEqual(assembly.assembly_accession, 'GCA_922984935')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_to_one_relations_assembly(self):
        eds = ena()
        assembly = eds.get_one('assembly', 'GCA_922984935.2')

        self.assertIsNotNone(assembly)
        study = assembly.study
        sample = assembly.sample
        taxon = assembly.taxon

        self.assertIsNotNone(study)
        self.assertEqual(study.type, 'study')
        self.assertEqual(study.id, 'PRJEB49353')
        self.assertIsNotNone(sample)
        self.assertEqual(sample.type, 'sample')
        self.assertEqual(sample.id, 'SAMEA7524400')
        self.assertIsNotNone(taxon)
        self.assertEqual(taxon.type, 'taxon')
        self.assertEqual(taxon.id, '9662')

    def test_get_to_many_relations_assembly(self):
        eds = ena()
        assembly = eds.get_one('assembly', 'GCA_922984935.2')

        self.assertIsNotNone(assembly)
        runs = list(assembly.runs)
        run_ids = [run.id for run in runs]
        expected_ids = set(assembly.run_accession.split(';'))

        self.assertTrue(runs)
        self.assertEqual(set(run_ids), expected_ids)
        self.assertEqual(len(run_ids), len(expected_ids))
        self.assertIn('ERR6688402', run_ids)
        for run in runs:
            self.assertEqual(run.type, 'read_run')

    def test_get_to_one_relations_read_run(self):
        eds = ena()
        run = eds.get_one('read_run', 'ERR6688402')

        self.assertIsNotNone(run)
        sample = run.sample
        experiment = run.experiment

        self.assertIsNotNone(sample)
        self.assertEqual(sample.type, 'sample')
        self.assertEqual(sample.id, 'SAMEA7524440')
        self.assertIsNotNone(experiment)
        self.assertEqual(experiment.type, 'read_experiment')
        self.assertEqual(experiment.id, 'ERX6313171')
        self.assertEqual(experiment.sample.id, sample.id)
        self.assertEqual(experiment.study.type, 'study')
        self.assertEqual(experiment.study.id, run.study_accession)
        self.assertEqual(sample.taxon.type, 'taxon')
        self.assertEqual(sample.taxon.id, run.tax_id)
        self.assertEqual(run.instrument_platform, 'ILLUMINA')
        self.assertEqual(run.library_strategy, 'Hi-C')
        self.assertIn('library_name', run.attributes)
        self.assertIn('library_construction_protocol', run.attributes)

    def test_get_to_many_relations_read_experiment(self):
        eds = ena()
        experiment = eds.get_one('read_experiment', 'ERX6313171')

        self.assertIsNotNone(experiment)
        runs = list(experiment.runs)

        self.assertTrue(runs)
        self.assertIn('ERR6688402', [run.id for run in runs])
        for run in runs:
            self.assertEqual(run.type, 'read_run')
            self.assertEqual(run.experiment_accession, experiment.id)
