# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List

import tol.jira.jira_methods as jm
from tol.core import DataSource
from tol.jira.jira_auth import JiraAuth


class JiraDataSource(DataSource):

    def __init__(self, config):
        super().__init__(config, expected=['url', 'api_token'])

    def get_specimens_for_treeval(self, page_number=1, page_size=1, filter_='', sort_by=''):

        page_size = int(page_size)
        page_number = int(page_number)

        jql_field_map = {
            'tolid': ("'Sample ID'", 'contains'),
            'species_name': ("'Species Name'", 'contains'),
            'jira_issue': ('key', 'equals'),
            'jira_issue_link': ('key', 'equals'),
            'jira_issue_last_updated': ('updated', 'equals'),
            'assignee': ("'Assignee'", 'equals'),
            'jbrowse_link': ("'Treeval'", 'equals')
        }

        ja = JiraAuth(url=self.url, password=self.api_token)
        jql_request = jm.apply_filter_sort_to_jql(
            "project in (GRIT,RC) AND 'Treeval' is not EMPTY",
            jql_field_map, filter_, sort_by)

        # Return all results for page until the number requested.
        results = ja.auth_jira.search_issues(jql_request, maxResults=0)

        entries_len = len(results)
        offset = page_size * (page_number - 1)

        page_first_row = offset + 1
        page_last_row = offset + page_size

        if entries_len < page_last_row:
            filtered_jira_results = results[page_first_row - 1:entries_len]
        else:
            filtered_jira_results = results[page_first_row - 1:page_last_row]

        entries = []
        for i in filtered_jira_results:
            issue = ja.auth_jira.issue(i)
            entry = {}

            entry['tolid'] = jm.get_species_id(issue)
            entry['species_name'] = jm.get_species_name(issue)
            entry['jira_issue'] = issue.key
            entry['jira_issue_link'] = f'https://{ja.jira_path}/browse/{issue.key}'
            entry['jira_issue_last_updated'] = str(issue.fields.updated)
            entry['jbrowse_link'] = jm.get_jbrowse_link(issue)
            entry['assignee'] = str(issue.fields.assignee)
            entries.append(entry)

        return {'total': entries_len, 'data': entries}

    def get_specimen_for_treeval(self, tolid):
        return self.get_specimens_for_treeval(1, 1, f'[tolid={tolid}]', 'tolid')[0]

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()

    @property
    def supported_types(self) -> List:
        raise NotImplementedError()
