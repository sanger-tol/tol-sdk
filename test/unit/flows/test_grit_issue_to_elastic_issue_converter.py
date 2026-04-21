# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase)

from dateutil.tz import tzlocal

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
    GritIssueToElasticIssueConverter
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
        return ['issue']

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


class TestGritIssueToElasticIssueConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceRelational2(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GritIssueToElasticIssueConverter(
            data_object_factory=destination.data_object_factory,
            config=GritIssueToElasticIssueConverter.Config()
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
                'project': 'TEST',
                'issue_type': 'Bug',
                'status': 'Ready for Staging',
                'sprint': [
                    'name=Sprint 0,'
                    'startDate=2019-02-05T09:00:00.000Z,endDate=2019-02-06T17:00:00.000Z',
                    'name=Sprint 1,'
                    'startDate=2020-02-05T09:00:00.000Z,endDate=2020-02-06T17:00:00.000Z'
                ],
                'story_points': 8,
                'status_changes': [
                    {
                        'this_status': 'Backlog',
                        'next_status': 'In Progress',
                        'start_date': datetime(2020, 2, 2),
                        'end_date': datetime(2020, 2, 3)
                    }, {
                        'this_status': 'In Progress',
                        'next_status': 'Ready for Staging',
                        'start_date': datetime(2020, 2, 3),
                        'end_date': datetime(2020, 2, 4)
                    }
                ]},
            to_one={
                'reporter': user,
                'assignee': user
            }
        )

        converteds = converter.convert(issue)
        ret1 = next(converteds)
        self.assertEqual('KEY-123', ret1.id)
        self.assertEqual('issue', ret1.type)
        self.assertEqual(ret1.attributes, {
            'created': datetime(2020, 2, 2),
            'in_progress_date': datetime(2020, 2, 3),
            'ready_for_staging_date': datetime(2020, 2, 4),
            'assignee_name': 'test',
            'story_points': 8,
            'number_of_sprints': 2,
            'jira_project': 'TEST',
            'issue_type': 'Bug',
            'original_story_points': None,
            'original_estimate': None,
            'remaining_estimate': None,
            'status': 'Ready for Staging',
            'first_sprint_start_date': datetime(2019, 2, 5, 9, 0, 0, tzinfo=tzlocal()),
            'first_sprint_end_date': datetime(2019, 2, 6, 17, 0, 0, tzinfo=tzlocal()),
            'first_sprint_name': 'Sprint 0',
            'last_sprint_start_date': datetime(2020, 2, 5, 9, 0, 0, tzinfo=tzlocal()),
            'last_sprint_end_date': datetime(2020, 2, 6, 17, 0, 0, tzinfo=tzlocal()),
            'last_sprint_name': 'Sprint 1',
        })

        with self.assertRaises(StopIteration):
            next(converteds)
