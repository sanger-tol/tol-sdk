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
    StsManifestToElasticManifestConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['manifest', 'compliance_status', 'manifest_status', 'project',
                'sampleset', 'shipment_status']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_manifest = RelationshipConfig()
        rc_manifest.to_one = {
            'project': 'project',
            'manifest_status': 'sampleset_status',
            'compliance_status': 'compliance_status',
            'sampleset': 'sampleset',
            'shipment_status': 'shipment_status'
        }
        return {
            'manifest': rc_manifest
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
        pass


class _MockDataSource(DataSource, Relational):

    @property
    def supported_types(self):
        return ['manifest', 'sampleset']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_manifest = RelationshipConfig()
        rc_manifest.to_one = {
            'sampleset': 'sampleset',
        }
        return {
            'manifest': rc_manifest
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
        pass


class TestStsManifestToElasticManifestConverter(TestCase):
    def test_convert(self):
        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsManifestToElasticManifestConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        project = CoreDataObject(
            id_='test_project',
            type_='project',
            attributes={'programme': 'test_programme'}
        )
        status = CoreDataObject(
            id_='test_status',
            type_='manifest_status',
            attributes={'status': 'COMPLETE'}
        )
        compliance_status = CoreDataObject(
            id_='test_compliance_status',
            type_='compliance_status',
            attributes={'status': 'PASSED'}
        )
        shipment_status = CoreDataObject(
            id_='test_shipment_status',
            type_='shipment_status',
            attributes={'status': 'SHIPPED'}
        )
        sampleset = CoreDataObject(
            id_='test_sampleset',
            type_='sampleset'
        )
        manifest = CoreDataObject(
            id_='test_manifest',
            type_='manifest',
            attributes={
                'copo_profile_title': 'COPO1',
                'submit_date': datetime.datetime(2024, 4, 4),
                'update_date': datetime.datetime(2024, 5, 5),
                'accept_date': datetime.datetime(2024, 6, 6),
                'receive_date': datetime.datetime(2024, 6, 7),
                'reject_date': datetime.datetime(2024, 7, 7),
                'archive_date': datetime.datetime(2024, 8, 8),
                'status_updated_at': datetime.datetime(2024, 9, 9),
                'shipment_status_updated_at': datetime.datetime(2024, 10, 10),
                'research_governance_status': 'PASSED',
                'rg_status_updated_at': datetime.datetime(2024, 11, 11),
                'wildlife_and_env_status': 'PASSED',
                'wildlife_status_updated_at': datetime.datetime(2024, 12, 12),
                'bio_safety_overall_status': 'PASSED',
                'bio_safety_overall_status_updated_at': datetime.datetime(2024, 12, 13),
            },
            to_one={
                'project': project,
                'manifest_status': status,
                'compliance_status': compliance_status,
                'sampleset': sampleset,
                'shipment_status': shipment_status
            }
        )

        converteds = converter.convert(manifest)
        ret1 = next(converteds)
        self.assertEqual('test_manifest', ret1.id)
        self.assertEqual('manifest', ret1.type)
        self.assertEqual(ret1.attributes, {
            'project': 'test_project',
            'programme': 'test_programme',
            'status': 'COMPLETE',
            'copo_profile_title': 'COPO1',
            'submit_date': datetime.datetime(2024, 4, 4),
            'update_date': datetime.datetime(2024, 5, 5),
            'accept_date': datetime.datetime(2024, 6, 6),
            'receive_date': datetime.datetime(2024, 6, 7),
            'reject_date': datetime.datetime(2024, 7, 7),
            'archive_date': datetime.datetime(2024, 8, 8),
            'status_updated_at': datetime.datetime(2024, 9, 9),
            'shipment_status_updated_at': datetime.datetime(2024, 10, 10),
            'research_governance_status': 'PASSED',
            'rg_status_updated_at': datetime.datetime(2024, 11, 11),
            'wildlife_and_env_status': 'PASSED',
            'wildlife_status_updated_at': datetime.datetime(2024, 12, 12),
            'bio_safety_overall_status': 'PASSED',
            'bio_safety_overall_status_updated_at': datetime.datetime(2024, 12, 13),
            'shipment_status': 'SHIPPED',
            'compliance_status': 'PASSED'
        })
        self.assertEqual(ret1.sampleset.id, 'test_sampleset')

        with self.assertRaises(StopIteration):
            next(converteds)
