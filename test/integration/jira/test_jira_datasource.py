# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime
from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter,
    core_data_object
)
from tol.jira import (
    JiraDataSource, create_jira_datasource
)


def jira_data_source() -> JiraDataSource:
    jds = create_jira_datasource(
        jira_url=os.getenv('JIRA_URL'),
        jira_api_key=os.getenv('JIRA_API_KEY')
    )
    cdo = core_data_object(jds)
    return cdo, jds


class TestJiraDataSource(TestCase):

    def test_attribute_types(self):
        _, jds = jira_data_source()

        assert 'issue' in jds.attribute_types
        assert jds.attribute_types['issue']['project'] == 'str'
        assert jds.attribute_types['issue']['created'] == 'datetime'
        assert jds.attribute_types['issue']['original_story_points'] == 'float'
        assert jds.attribute_types['issue']['status_changes'] == 'List[Dict[str, Any]]'

    def test_relationship_config(self):
        _, jds = jira_data_source()

        assert 'issue' in jds.relationship_config
        assert jds.relationship_config['issue'].to_one['reporter'] == 'user'

    def test_get_by_id(self):
        _, jds = jira_data_source()

        ret = jds.get_by_ids('issue', ['RC-123'])
        obj1 = next(ret)
        self.assertEqual('RC-123', obj1.id)
        # Just pick out a few attributes here to test
        self.assertEqual(obj1.sample_id, 'ilWatBina1')
        self.assertEqual(obj1.manual_joins, 6.0)
        self.assertEqual(obj1.resolved, datetime(2022, 2, 7, 17, 58, 2))
        self.assertEqual(obj1.project, 'ToL Rapid Curation')
        self.assertEqual(obj1.curation_files, [
            'Primary TPF',
            'Haplotig TPF',
            'Chromsome List'
        ])
        self.assertEqual(obj1.reporter.emailAddress, 'kk16@sanger.ac.uk')
        self.assertEqual(obj1.status_changes, [
            {
                'this_status': 'Open',
                'next_status': 'Decontamination',
                'start_date': datetime(2021, 11, 6, 0, 0, 8),
                'end_date': datetime(2021, 11, 6, 3, 0, 15)
            }, {
                'this_status': 'Decontamination',
                'next_status': 'HiC Building',
                'start_date': datetime(2021, 11, 6, 3, 0, 15),
                'end_date': datetime(2021, 11, 11, 10, 47)
            }, {
                'this_status': 'HiC Building',
                'next_status': 'curation',
                'start_date': datetime(2021, 11, 11, 10, 47),
                'end_date': datetime(2021, 11, 22, 15, 14, 33)
            }, {
                'this_status': 'curation',
                'next_status': 'Curation QC',
                'start_date': datetime(2021, 11, 22, 15, 14, 33),
                'end_date': datetime(2022, 2, 2, 14, 14, 39)
            }, {
                'this_status': 'Curation QC',
                'next_status': 'Post Processing++',
                'start_date': datetime(2022, 2, 2, 14, 14, 39),
                'end_date': datetime(2022, 2, 3, 13, 55, 36)
            }, {
                'this_status': 'Post Processing++',
                'next_status': 'In Submission',
                'start_date': datetime(2022, 2, 3, 13, 55, 36),
                'end_date': datetime(2022, 2, 4, 9, 56, 23)
            }, {
                'this_status': 'In Submission',
                'next_status': 'Submitted',
                'start_date': datetime(2022, 2, 4, 9, 56, 23),
                'end_date': datetime(2022, 2, 7, 17, 58, 1)
            }, {
                'this_status': 'Submitted',
                'next_status': 'Done',
                'start_date': datetime(2022, 2, 7, 17, 58, 1),
                'end_date': datetime(2022, 2, 7, 17, 58, 2)
            }
        ])

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, jds = jira_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'project': {'eq': {'value': 'RC'}},
            'id': {'in_list': {'value': ['RC-1', 'RC-2', 'RC-5']}}
        }
        ret = jds.get_list('issue', object_filters=f)
        obj1 = next(ret)
        self.assertEqual('RC-1', obj1.id)
        self.assertEqual(obj1.sample_id, 'ilPerRhom1')
        self.assertEqual(obj1.manual_joins, 11)
        self.assertEqual(obj1.resolved, datetime(2021, 7, 26, 15, 26, 46))
        self.assertEqual(obj1.project, 'ToL Rapid Curation')
        self.assertEqual(obj1.curation_files, [
            'Primary TPF',
            'Haplotig TPF',
            'Chromsome List'
        ])
        self.assertEqual(obj1.reporter.emailAddress, 'kk16@sanger.ac.uk')

        obj2 = next(ret)
        self.assertEqual('RC-2', obj2.id)
        self.assertEqual(obj2.sample_id, 'ilCamMarg1')
        self.assertEqual(obj2.manual_joins, 6)
        self.assertEqual(obj2.resolved, datetime(2021, 8, 13, 19, 5, 51))
        self.assertEqual(obj2.reporter.emailAddress, 'kk16@sanger.ac.uk')

        obj3 = next(ret)
        self.assertEqual('RC-5', obj3.id)
        self.assertEqual(obj3.sample_id, 'ilHydFurc1')
        self.assertEqual(obj3.manual_joins, 14)
        self.assertEqual(obj3.resolved, datetime(2021, 8, 13, 19, 5, 52))
        self.assertEqual(obj3.reporter.emailAddress, 'kk16@sanger.ac.uk')

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list_page_sort_custom(self):
        _, jds = jira_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'project': {'eq': {'value': 'RC'}},
            'id': {'in_list': {'value': ['RC-1', 'RC-2', 'RC-5', 'RC-1579']}}
        }
        ret, total = jds.get_list_page(
            'issue',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-manual_joins'
        )
        assert total == 4
        assert len(ret) == 3
        obj3 = ret[0]
        self.assertEqual('RC-5', obj3.id)
        self.assertEqual(obj3.sample_id, 'ilHydFurc1')
        self.assertEqual(obj3.manual_joins, 14)
        self.assertEqual(obj3.resolved, datetime(2021, 8, 13, 19, 5, 52))
        self.assertEqual(obj3.reporter.emailAddress, 'kk16@sanger.ac.uk')

        obj1 = ret[1]
        self.assertEqual('RC-1', obj1.id)
        self.assertEqual(obj1.sample_id, 'ilPerRhom1')
        self.assertEqual(obj1.manual_joins, 11)
        self.assertEqual(obj1.resolved, datetime(2021, 7, 26, 15, 26, 46))
        self.assertEqual(obj1.reporter.emailAddress, 'kk16@sanger.ac.uk')

        obj2 = ret[2]
        self.assertEqual('RC-2', obj2.id)
        self.assertEqual(obj2.sample_id, 'ilCamMarg1')
        self.assertEqual(obj2.manual_joins, 6)
        self.assertEqual(obj2.resolved, datetime(2021, 8, 13, 19, 5, 51))
        self.assertEqual(obj2.reporter.emailAddress, 'kk16@sanger.ac.uk')

    def test_get_list_page_sort_id(self):
        _, jds = jira_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'project': {'eq': {'value': 'RC'}},
            'id': {'in_list': {'value': ['RC-1', 'RC-2', 'RC-5', 'RC-1579']}}
        }
        ret, total = jds.get_list_page(
            'issue',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-id'
        )
        assert total == 4
        assert len(ret) == 3
        self.assertEqual('RC-1579', ret[0].id)
        self.assertEqual('RC-5', ret[1].id)
        self.assertEqual('RC-2', ret[2].id)

    def test_get_list_page_sort_relation(self):
        _, jds = jira_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'project': {'eq': {'value': 'RC'}},
            'id': {'in_list': {'value': ['RC-344', 'RC-5', 'RC-9', 'RC-1579']}}
        }
        ret, total = jds.get_list_page(
            'issue',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-reporter.emailAddress'
        )
        assert total == 4
        assert len(ret) == 3
        self.assertEqual('RC-1579', ret[0].id)  # sm15
        self.assertEqual('RC-344', ret[1].id)  # mu2
        self.assertEqual('RC-5', ret[2].id)  # kk16
        # RC-9 is cz3
