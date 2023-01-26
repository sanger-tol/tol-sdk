# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import tol.jira.jira_methods as jm
from tol.jira.jira_auth import JiraAuth


class Jira:
    def __init__(self, config, api_token='DEFAULT'):
        if api_token == 'DEFAULT':
            self.api_token = config['api_token']
        else:
            self.api_token = api_token
        self.url = config['url']

    def get_specimens_for_treeval(self, page_number=1, page_size=1, filter_='', sort_by=''):

        page_size = int(page_size)
        page_number = int(page_number)

        jql_field_map = {'tolid': "'Sample ID'",
                         'species_name': "'Species Name'",
                         'jira_issue': 'key',
                         'jira_issue_last_updated': 'updated',
                         'jbrowse_link': "'Datatype Available'"}

        ja = JiraAuth(url=self.url, password=self.api_token)
        jql_request = jm.apply_filter_sort_to_jql('project in (GRIT,RC)',
                                                  jql_field_map, filter_, sort_by)

        # Return all results for page until the number requested.
        results = ja.auth_jira.search_issues(jql_request)

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
            entry['jira_issue_last_updated'] = issue.fields.updated
            entry['jbrowse_link'] = ''
            entries.append(entry)

        return {'total': entries_len, 'data': entries}

    def get_specimen_for_treeval(self, tolid):
        return self.get_specimens_for_treeval(1, 1, f'[tolid={id}]', 'tolid')[0]
