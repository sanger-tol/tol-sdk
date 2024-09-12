# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
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
    GritIssueToElasticCurationConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['issue', 'user']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_issue = RelationshipConfig()
        rc_issue.to_one = {
            'reporter': 'user',
            'assignee': 'user'
        }
        return {
            'issue': rc_issue
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSourceRelational2(DataSource, Relational):

    @property
    def supported_types(self):
        return ['curation', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_curation = RelationshipConfig()
        rc_curation.to_one = {
            'tolid': 'tolid'
        }
        return {
            'curation': rc_curation
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestGritIssueToElasticCurationConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceRelational2(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GritIssueToElasticCurationConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        user = CoreDataObject(
            id_='test_user',
            type_='user',
            attributes={
                'email': 'test@test.com',
                'name': 'test',
                'displayName': 'Test User'
            }
        )
        issue = CoreDataObject(
            id_='KEY-123',
            type_='issue',
            attributes={
                'created': datetime(2020, 2, 2),
                'sample_id': 'abCdeFghi1',
                'description': 'Ignore',
                'status_changes': [
                    {
                        'this_status': 'Open',
                        'next_status': 'Mid Range',
                        'start_date': datetime(2020, 2, 2),
                        'end_date': datetime(2020, 2, 3)
                    }, {
                        'this_status': 'Open',
                        'next_status': 'Closed',
                        'start_date': datetime(2020, 2, 3),
                        'end_date': datetime(2020, 2, 4)
                    }
                ],
                'assembly_statistics': 'scaffolds\ntotal 333046658 333047658\ncount 41 36\nN50 11581856 11581856\nL50 13 13\nN90 7014107 7711609\nL90 27 27\n\ncontigs\ntotal 333046218 333046218\ncount 44 44\nN50 11581856 11581856\nL50 13 13\nN90 7014107 7014107\nL90 27 27\n',  # noqa E501
                'chromosome_result': 'found 31 autosomes and W and Z and MT\nTotal length 333047658\nChr length 332949469\nChr length 99.97 %\n',  # noqa E501
            },
            to_one={
                'reporter': user,
                'assignee': user
            }
        )
        converteds = converter.convert(issue)
        ret1 = next(converteds)
        self.assertEqual('KEY-123', ret1.id)
        self.assertEqual('curation', ret1.type)
        self.assertEqual(ret1.attributes, {
            'created': datetime(2020, 2, 2),
            'mid_range_date': datetime(2020, 2, 3),
            'closed_date': datetime(2020, 2, 4),
            'scaffolds_total_before': 333046658,
            'scaffolds_total_after': 333047658,
            'scaffolds_total_change_per': 0.0003002582298844146,
            'scaffolds_count_before': 41,
            'scaffolds_count_after': 36,
            'scaffolds_count_change_per': -12.195121951219512,
            'scaffolds_n50_before': 11581856,
            'scaffolds_n50_after': 11581856,
            'scaffolds_n50_change_per': 0.0,
            'scaffolds_l50_before': 13,
            'scaffolds_l50_after': 13,
            'scaffolds_l50_change_per': 0.0,
            'scaffolds_n90_before': 7014107,
            'scaffolds_n90_after': 7711609,
            'scaffolds_n90_change_per': 9.944273732921383,
            'scaffolds_l90_before': 27,
            'scaffolds_l90_after': 27,
            'scaffolds_l90_change_per': 0.0,
            'contigs_total_before': 333046218,
            'contigs_total_after': 333046218,
            'contigs_total_change_per': 0.0,
            'contigs_count_before': 44,
            'contigs_count_after': 44,
            'contigs_count_change_per': 0.0,
            'contigs_n50_before': 11581856,
            'contigs_n50_after': 11581856,
            'contigs_n50_change_per': 0.0,
            'contigs_l50_before': 13,
            'contigs_l50_after': 13,
            'contigs_l50_change_per': 0.0,
            'contigs_n90_before': 7014107,
            'contigs_n90_after': 7014107,
            'contigs_n90_change_per': 0.0,
            'contigs_l90_before': 27,
            'contigs_l90_after': 27,
            'contigs_l90_change_per': 0.0,
            'chr_ass': 'found 31 autosomes',
            'ass_percent': '99.97',
            'assignee_name': 'test'
        })
        self.assertEqual(ret1.tolid.id, 'abCdeFghi1')

        with self.assertRaises(StopIteration):
            next(converteds)
