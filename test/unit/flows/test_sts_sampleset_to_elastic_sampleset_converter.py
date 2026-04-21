# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
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
    StsSamplesetToElasticSamplesetConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sampleset', 'sampleset_legal', 'sampleset_research_governance',
                'compliance_status', 'sampleset_status', 'project', 'gal',
                'legal_compliance_processor', 'sampleset_research_governance_processor',
                'sampleset_manager', 'user']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sampleset = RelationshipConfig()
        rc_sampleset.to_one = {
            'gal': 'gal',
            'project': 'project',
            'sampleset_status': 'sampleset_status'
        }
        rc_sampleset.to_many = {
            'sampleset_legals': 'sampleset_legal',
            'sampleset_research_governances': 'sampleset_research_governance',
            'legal_compliance_processors': 'legal_compliance_processor',
            'sampleset_research_governance_processors': 'sampleset_research_governance_processor',
            'sampleset_managers': 'sampleset_manager'
        }
        rc_sampleset_research_governance = RelationshipConfig()
        rc_sampleset_research_governance.to_one = {
            'compliance_status': 'compliance_status'
        }
        rc_legal_compliance_processor = RelationshipConfig()
        rc_legal_compliance_processor.to_one = {
            'user': 'user'
        }
        rc_research_governance_processor = RelationshipConfig()
        rc_research_governance_processor.to_one = {
            'user': 'user'
        }
        rc_sampleset_managers = RelationshipConfig()
        rc_sampleset_managers.to_one = {
            'user': 'user'
        }
        return {
            'sampleset': rc_sampleset,
            'sampleset_research_governance': rc_sampleset_research_governance,
            'legal_compliance_processor': rc_legal_compliance_processor,
            'sampleset_research_governance_processor': rc_research_governance_processor,
            'sampleset_manager': rc_sampleset_managers
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if relationship_name == 'sampleset_legals':
            yield source._host.data_object_factory(
                id_='test_legal',
                type_='sampleset_legal',
                attributes={
                    'status': 'PASSED',
                    'status_updated_at': datetime.datetime(2024, 8, 8),
                    'contract': 'test_contract',
                    'reference': 'test_reference',
                    'comment': 'test_comment'
                }
            )

        if relationship_name == 'legal_compliance_processors':
            yield source._host.data_object_factory(
                id_='test_lcp',
                type_='legal_compliance_processor',
                attributes={
                },
                to_one={
                    'user': source._host.data_object_factory(
                        id_='test_user',
                        type_='user',
                        attributes={'fullname': 'Test User'}
                    )
                }
            )
        if relationship_name == 'sampleset_research_governance_processors':
            yield source._host.data_object_factory(
                id_='test_rgp',
                type_='sampleset_research_governance_processor',
                attributes={
                },
                to_one={
                    'user': source._host.data_object_factory(
                        id_='test_user',
                        type_='user',
                        attributes={'fullname': 'Test RGP User'}
                    )
                }
            )
        if relationship_name == 'sampleset_managers':
            yield source._host.data_object_factory(
                id_='test_ssm',
                type_='sampleset_manager',
                attributes={
                },
                to_one={
                    'user': source._host.data_object_factory(
                        id_='test_user',
                        type_='user',
                        attributes={'fullname': 'Test Manager User'}
                    )
                }
            )
        if relationship_name == 'sampleset_research_governances':
            yield source._host.data_object_factory(
                id_='test_rg',
                type_='sampleset_research_governance',
                attributes={
                    'research_governance_type': 'TEST',
                    'updated_at': datetime.datetime(2024, 9, 9)
                },
                to_one={
                    'compliance_status': source._host.data_object_factory(
                        id_='test_status',
                        type_='compliance_status',
                        attributes={'status': 'PASSED'}
                    )
                }
            )


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['sampleset']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSamplesetToElasticSamplesetConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsSamplesetToElasticSamplesetConverter(
            data_object_factory=destination.data_object_factory,
            config=StsSamplesetToElasticSamplesetConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        project = CoreDataObject(
            id_='test_project',
            type_='project',
            attributes={'programme': 'test_programme'}
        )
        gal = CoreDataObject(
            id_='test_gal',
            type_='gal',
            attributes={
                'name': 'Test Gal',
                'abbreviation': 'TESTGAL'
            }
        )
        status = CoreDataObject(
            id_='test_status',
            type_='sampleset_status',
            attributes={'status': 'COMPLETE'}
        )
        sampleset = CoreDataObject(
            id_='test_sampleset',
            type_='sampleset',
            attributes={
                'name': 'test_sampleset',
                'submit_date': datetime.datetime(2024, 4, 4),
                'expected_manifest_date': datetime.datetime(2024, 6, 6),
                'shipping_date': datetime.datetime(2024, 5, 5),
                'status_updated_at': datetime.datetime(2024, 7, 7),
                'num_expected_species': 10,
                'num_expected_samples': 20,
                'released_to_lab': True
            },
            to_one={
                'gal': gal,
                'project': project,
                'sampleset_status': status
            }
        )

        converteds = converter.convert(sampleset)
        ret1 = next(converteds)
        self.assertEqual('test_sampleset', ret1.id)
        self.assertEqual('sampleset', ret1.type)
        self.assertEqual(ret1.attributes, {
            'project': 'test_project',
            'programme': 'test_programme',
            'status': 'COMPLETE',
            'name': 'test_sampleset',
            'submit_date': datetime.datetime(2024, 4, 4),
            'expected_manifest_date': datetime.datetime(2024, 6, 6),
            'shipping_date': datetime.datetime(2024, 5, 5),
            'status_updated_at': datetime.datetime(2024, 7, 7),
            'num_expected_species': 10,
            'num_expected_samples': 20,
            'released_to_lab': True,
            'gal_abbreviation': 'TESTGAL',
            'legal_status': 'PASSED',
            'legal_status_updated_at': datetime.datetime(2024, 8, 8),
            'legal_contract': 'test_contract',
            'legal_reference': 'test_reference',
            'legal_comment': 'test_comment',
            'rg_status_test': 'PASSED',
            'rg_status_updated_at_test': datetime.datetime(2024, 9, 9),
            'legal_compliance_processors': ['Test User'],
            'research_governance_processors': ['Test RGP User'],
            'managers': ['Test Manager User']
        })

        with self.assertRaises(StopIteration):
            next(converteds)
