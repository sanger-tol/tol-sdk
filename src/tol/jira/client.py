# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional, Tuple

from atlassian import Jira

import requests

from .converter import JiraIssues


class JiraClient:
    """
    Takes Jira API transfers and connects to a remote
    Jira API.
    """

    def __init__(
        self,
        jira_url: str,
        jira_api_key: str,
    ) -> None:
        self.jira = Jira(
            url=jira_url,
            token=jira_api_key
        )
        self.__jira_url = jira_url
        self.__jira_api_key = jira_api_key
        self.__type_mappings = {
            'number': 'float',
            'array': 'List[str]',
            'datetime': 'datetime'
        }

    def get_list_page(
        self,
        object_type: str,
        page: int,
        page_size: int,
        filter_string: Optional[str] = None
    ) -> Tuple[JiraIssues, int]:
        if object_type == 'issue':
            return self.__get_issues_page(
                page=page,
                page_size=page_size,
                filter_string=filter_string
            )

    def get_detail(
        self,
        object_type: str,
        issue_ids: list[str]
    ) -> JiraIssues:
        """
        Gets a single Jira issue
        """
        issues_string = '","'.join(issue_ids)
        issues, _ = self.get_list_page(
            object_type=object_type,
            filter_string=f'key in ("{issues_string}")',
            page_size=len(issue_ids),
            page=1
        )
        return issues

    def get_fields(self) -> dict:
        """
        Gets the fields of a Jira issue
        There doesn't seem to be a method for this on the JIRA class
        """
        response = requests.get(
            self.__jira_url + '/rest/api/latest/field',
            headers={
                'Authorization': f'Bearer {self.__jira_api_key}',
            }
        )
        fields = {}
        for field in response.json():
            jira_type = field['schema']['type'] if 'schema' in field else 'string'
            jira_item_type = field['schema']['items'] if 'schema' in field \
                and 'items' in field['schema'] else 'string'

            fields[field['id']] = {
                'display_name': field['name'],
                'system_name': field['name'].lower().replace('/', '').replace(' ', '_'),
                'type': self.__type_mappings[jira_type]
                if jira_type in self.__type_mappings else 'str',
                'jira_type': jira_type,
                'jira_item_type': jira_item_type,
                'clause_name': field['clauseNames'][0]
                if 'clauseNames' in field and len(field['clauseNames']) > 0 else field['name'],
                'relation': 'user' if jira_type == 'user' else None
            }
        return fields

    def get_issue_status_changelog(self, issue_id: str) -> dict:
        """
        Gets the issue status changelog of a Jira issue
        """
        print(f'Getting issue status changelog for {issue_id}')
        issue_status_changelog = self.jira.get_issue_status_changelog(
            issue_id=issue_id
        )
        return issue_status_changelog

    def __get_issues_page(
        self,
        page: int,
        page_size: int,
        filter_string: Optional[str] = None
    ) -> JiraIssues:
        """
        Gets a page of Jira issues
        """
        issues = self.jira.jql(
            jql=filter_string,
            start=page_size * (page - 1),
            limit=page_size,
            expand='changelog'
        )
        return issues['issues'], issues['total']
