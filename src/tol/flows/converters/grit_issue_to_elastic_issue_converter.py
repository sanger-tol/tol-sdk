# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from typing import Iterable

from dateutil.parser import parse as dateutil_parse

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GritIssueToElasticIssueConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        status_changes = {
            self.__sanitise_attribute_name(sc['next_status']) + '_date': sc['end_date']
            for sc in data_object.status_changes
            if sc.get('next_status') is not None
        }
        sprints = self.__parse_sprint(data_object.sprint)

        sprint_attributes = {
            'number_of_sprints': len(sprints),
            'first_sprint_start_date': sprints[0]['startDate'] if sprints else None,
            'first_sprint_end_date': sprints[0]['endDate'] if sprints else None,
            'first_sprint_name': sprints[0]['name'] if sprints else None,
            'last_sprint_start_date': sprints[-1]['startDate'] if sprints else None,
            'last_sprint_end_date': sprints[-1]['endDate'] if sprints else None,
            'last_sprint_name': sprints[-1]['name'] if sprints else None,
        }

        yield self._data_object_factory(
            'issue',
            data_object.id,
            attributes={
                'issue_type': data_object.issue_type,
                'jira_project': data_object.project,
                'created': data_object.created,
                'status': data_object.status,
                'assignee_name': data_object.assignee.name if data_object.assignee else None,
                'original_story_points': data_object.original_story_points,
                'story_points': data_object.story_points,
                'original_estimate': data_object.original_estimate,
                'remaining_estimate': data_object.remaining_estimate
            } | status_changes | sprint_attributes
        )

    def __sanitise_attribute_name(self, name: str) -> str:
        return re.sub(r'\s+', '_', name.lower())

    def __parse_sprint(self, sprint: list | None) -> str:
        sprints = []
        if sprint is None:
            return sprints
        for s in sprint:
            match_end = re.search(r'endDate=([^,\]]+)', s)
            match_name = re.search(r'name=([^,\]]+)', s)
            match_start = re.search(r'startDate=([^,\]]+)', s)

            if match_end and match_name and match_start and match_start.group(1) != '<null>' \
                    and match_end.group(1) != '<null>':
                start_date = dateutil_parse(match_start.group(1)) if match_start.group(1) else None
                end_date = dateutil_parse(match_end.group(1)) if match_end.group(1) else None
                sprints.append({
                    'name': match_name.group(1),
                    'startDate': start_date,
                    'endDate': end_date
                })
        return sprints
