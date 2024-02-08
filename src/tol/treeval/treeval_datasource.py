# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import re
from functools import cache
from typing import Dict, Iterable, Tuple

import pandas as pd

import requests

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import PageGetter


class TreevalDataSource(
    DataSource,
    PageGetter,
):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['url', 'api_token'])

    def _build_jira_query(self):
        return '{"jql":"status = curation and project in (RC,GRIT)","maxResults":1000,\
            "fields":["key", "priority", "fields", "updated", "customfield_12200",\
                 "customfield_11676", "customfield_11677", "summary", "assignee",\
                     "attachment", "description", "customfield_11643", "customfield_11605",\
                     "customfield_12800", "customfield_12802"]}'

    def _execute_jira_query(self, query):
        response = requests.post(
            url=f'https://{self.url}/rest/api/latest/search',
            headers={'Authorization': 'Bearer ' + self.api_token,
                     'Content-Type': 'application/json'},
            data=query
        )

        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to JIRA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response.json()

    def _parse_jira_output(self, response_text):

        issues = map(self._get_values_from_issue, response_text['issues'])

        return pd.DataFrame(issues)

    def _parse_decontamination_report(self, decon_data):
        tot_removed = ''
        tot_removed_pc = ''
        count_removed = ''
        count_removed_pc = ''
        largest_removed = ''
        is_abnormal = 'false'

        tot_removed_regex = \
            re.compile(r'Total length of scaffolds removed: ([0-9,]+) \(([0-9\.]+) %\)')
        count_removed_regex = re.compile(r'Scaffolds removed: ([0-9,]+) \(([0-9\.]+) %\)')
        largest_removed_regex = re.compile(r'Largest scaffold removed: \(([0-9,]+)\)')

        tot_rem = tot_removed_regex.search(decon_data)
        count_rem = count_removed_regex.search(decon_data)
        largest_rem = largest_removed_regex.search(decon_data)

        if tot_rem:
            tot_removed = tot_rem.group(1)
            tot_removed_pc = tot_rem.group(2)

        if count_rem:
            count_removed = count_rem.group(1)
            count_removed_pc = count_rem.group(2)

        if largest_rem:
            largest_removed = largest_rem.group(1)

        if 'Abnormal contamination report' in decon_data:
            is_abnormal = 'true'

        return tot_removed, tot_removed_pc, count_removed, \
            count_removed_pc, largest_removed, is_abnormal

    def _parse_description_for_stats(self, description):

        scaffold_l90 = '-'
        contig_l90 = '-'

        scaffold_l90_regex = re.compile(r'SCAFFOLD[ \t\n\r\f\v]N90 = [0-9]+, L90 = ([0-9]+)')
        contig_l90_regex = re.compile(r'CONTIG[ \t\n\r\f\v]N90 = [0-9]+, L90 = ([0-9]+)')

        sl90 = scaffold_l90_regex.search(description)
        cl90 = contig_l90_regex.search(description)

        if sl90:
            scaffold_l90 = sl90.groups(1)

        if cl90:
            contig_l90 = cl90.groups(1)

        return scaffold_l90, contig_l90

    def _get_values_from_issue(self, issue):

        key = issue['key']

        fields = issue['fields']
        priority = fields['priority']
        updated = pd.Timestamp(fields['updated'])
        species_name = self._parse_species_name(fields['customfield_11676'])

        tolid = self._parse_species_id(fields['summary'])
        tolid_assem = fields['customfield_11643']

        expected_karyotype = fields['customfield_11605']
        if not expected_karyotype:
            expected_karyotype = '-'

        con_filname = fields['customfield_11677']
        file_struct = con_filname.split('/')
        tolqc_project = file_struct[5]

        if tolqc_project == 'meier':
            tolqc_clade = file_struct[8]

        elif tolqc_project == 'badass':
            tolqc_project = 'lawniczak'
            tolqc_clade = 'badass'
        else:
            tolqc_clade = file_struct[7]

        species_name_parts = species_name.split(' ')
        if len(species_name_parts) > 1:
            tolqc_species_name = f'{species_name_parts[0]}_{species_name_parts[1]}'
        else:
            tolqc_species_name = ''

        # Treeval link
        treeval_val = fields['customfield_12800']

        if not treeval_val or 'jb_scaffold' not in treeval_val:
            treeval_val = \
                '{"jbrowse": "","jb_scaffold": "","start": "","btk_pr": "","btk_hp": "",\
                "higlass": "","taxon_id": ""}'

        treeval_data = json.loads(treeval_val)

        # Stats from description
        description = str(fields['description'])
        scaffold_l90, contig_l90 = self._parse_description_for_stats(description)

        # Parse decontamination
        decon_data = str(fields['customfield_12802'])
        tot_removed, tot_removed_pc, count_removed, count_removed_pc, \
            largest_removed, is_abnormal = self._parse_decontamination_report(decon_data)

        # Assignee
        assignee = fields['assignee']

        if assignee:
            display_name = assignee['displayName']
        else:
            display_name = 'Unassigned'

        # Hi-C Contact Map image
        hic_plot_path = ''
        if 'hic_plot' in treeval_data.keys():
            if treeval_data['hic_plot'] == 'Y':
                hic_plot_path = \
                    f'https://treeval.cog.sanger.ac.uk/pretextsnapshot_{tolid_assem}.png'

        # K-mer spectra image
        kmer_plot_path = ''
        if 'kmer_plot' in treeval_data.keys():
            if treeval_data['kmer_plot'] == 'Y':
                kmer_plot_path = \
                    f'https://treeval.cog.sanger.ac.uk/kmerspectra_{tolid_assem}.png'

        # jBrowse link
        if 'jbrowse' in treeval_data.keys():
            if treeval_data['jbrowse']:

                tolid = treeval_data['jbrowse']
                scaff = treeval_data['jb_scaffold']
                server = treeval_data['jb_server']

                if server == 'dev':
                    server_url = 'tol-dev'
                else:
                    server_url = 'tol'

                jbrowse_link = ('http://jbrowse.' + server_url
                                + '.sanger.ac.uk/jbrowse2/?config=config.json'
                                + '&assembly=' + tolid + '&session=spec-'
                                + '{%22views%22:[{%22assembly%22:%22'
                                + tolid + '%22,%22loc%22:%22' + scaff
                                + '%22,%22type%22:%22LinearGenomeView%22,%22tracks%22:[%22'
                                + tolid + '-ReferenceSequenceTrack%22]}]}')

            else:
                jbrowse_link = ''
        else:
            jbrowse_link = ''

        # BTK primary link
        if 'btk_pr' in treeval_data.keys():
            btk_pr = treeval_data['btk_pr']
            if btk_pr:
                btk_pr_link = (f'https://grit-btk.tol.sanger.ac.uk/view/{btk_pr}'
                               + f'/dataset/{btk_pr}.fa.ascc/blob')
            else:
                btk_pr_link = ''
        else:
            btk_pr_link = ''

        # BTK haplotigs link
        if 'btk_hp' in treeval_data.keys():
            btk_hp = treeval_data['btk_hp']
            if btk_hp:
                btk_hp_link = (f'https://grit-btk.tol.sanger.ac.uk/view/{btk_hp}'
                               + f'/dataset/{btk_hp}.fa.ascc/blob')
            else:
                btk_hp_link = ''
        else:
            btk_hp_link = ''

        # GoaT link
        if 'taxon_id' in treeval_data.keys():
            taxon_id = treeval_data['taxon_id']
            if taxon_id:
                goat_link = (f'https://goat.genomehubs.org/record?recordId={taxon_id}'
                             + '&result=taxon&taxonomy=ncbi')
            else:
                goat_link = ''
        else:
            goat_link = ''

        # HiGlass link
        if 'higlass' in treeval_data.keys():
            higlass_id = treeval_data['higlass']
            if higlass_id:
                higlass_link = f'https://grit-higlass.tol.sanger.ac.uk/l/?d={higlass_id}'
            else:
                higlass_link = ''
        else:
            higlass_link = ''

        # Start date
        if treeval_data['start'] != '':
            added_to_curation_date = pd.Timestamp(treeval_data['start'])
        else:
            added_to_curation_date = pd.Timestamp('1970-01-01T00:00:00.000+0100')

        # ToLQC link
        if tolqc_project not in ('tol-nematodes', 'genomeark'):
            tolqc_link = (f'https://tolqc.cog.sanger.ac.uk/{tolqc_project}/'
                          + f'{tolqc_clade}/{tolqc_species_name}/')
        else:
            tolqc_link = ''

        return {'tolid': tolid,
                'species_name': species_name,
                'priority': str(priority['id']),
                'jira_issue': key,
                'jira_issue_url': f'https://{self.url}/browse/{key}',
                'jira_issue_last_updated': updated,
                'added_to_curation': added_to_curation_date,
                'jbrowse_url': jbrowse_link,
                'assignee': display_name,
                'goat_url': goat_link,
                'higlass_url': higlass_link,
                'btk_pri_url': btk_pr_link,
                'btk_hap_url': btk_hp_link,
                'tolqc_url': tolqc_link,
                'hic_plot': hic_plot_path,
                'kmer_plot': kmer_plot_path,
                'scaffold_l90': scaffold_l90,
                'contig_l90': contig_l90,
                'expected_karyotype': str(expected_karyotype),
                'total_scaffolds_removed': str(tot_removed),
                'total_scaffolds_removed_pc': str(tot_removed_pc),
                'scaffolds_removed_count': str(count_removed),
                'scaffolds_removed_count_pc': str(count_removed_pc),
                'largest_scaffold_removed': largest_removed,
                'contamination_is_abnormal': is_abnormal
                }

    def _parse_species_name(self, species_name):
        if species_name:

            # Trim unused common name
            suffix = ' ()'
            if species_name.endswith(suffix):
                species_name = species_name[:-len(suffix)]

            return species_name
        else:
            return ''

    def _parse_species_id(self, summary):
        species_id = str(summary)

        if species_id != '':
            species_id = species_id.replace(' GenomeArk assembly', '')
            species_id = species_id.replace(' ERGA assembly', '')
            species_id = species_id.replace(' Darwin assembly', '')
            species_id = species_id.replace(' faculty assembly', '')
            species_id = species_id.replace(' ASG assembly', '')
            species_id = species_id.replace(' VGP assembly', '')
            species_id = species_id.replace(' external assembly', '')
            species_id = species_id.replace(' TOL assembly', '')
            species_id = species_id.replace(' assembly', '')

            return species_id
        else:
            return ''

    def _apply_contains_filter_to_specimens(self, object_filters, specimens):

        if 'tolid' in object_filters:
            specimens = specimens[specimens['tolid']
                                  .str.contains(object_filters['tolid'])]

        if 'species_name' in object_filters:
            specimens = specimens[specimens['species_name']
                                  .str.contains(object_filters['species_name'])]

        if 'jira_issue' in object_filters:
            specimens = specimens[specimens['jira_issue']
                                  .str.contains(object_filters['jira_issue'])]

        if 'jira_issue_link' in object_filters:
            specimens = specimens[specimens['jira_issue_link']
                                  .str.contains(object_filters['jira_issue_link'])]

        if 'jbrowse_link' in object_filters:
            specimens = specimens[specimens['jbrowse_link']
                                  .str.contains(object_filters['jbrowse_link'])]

        if 'assignee' in object_filters:
            specimens = specimens[specimens['assignee']
                                  .str.contains(object_filters['assignee'])]

        if 'jbrowse_status' in object_filters:
            specimens = specimens[specimens['jbrowse_status']
                                  .str.contains(object_filters['jbrowse_status'])]

        return specimens

    def _apply_range_filter_to_specimens(self, object_filters, specimens):

        if 'jira_issue_last_updated' in object_filters:
            last_updated_range = object_filters['jira_issue_last_updated']
            specimens = specimens[(specimens['jira_issue_last_updated']
                                  > pd.Timestamp(last_updated_range['from']))
                                  & (specimens['jira_issue_last_updated']
                                      < pd.Timestamp(last_updated_range['to']))]

        if 'added_to_curation' in object_filters:
            added_to_curation_range = object_filters['added_to_curation']
            specimens = specimens[(specimens['added_to_curation']
                                  > pd.Timestamp(added_to_curation_range['from']))
                                  & (specimens['added_to_curation']
                                      < pd.Timestamp(added_to_curation_range['to']))]

        return specimens

    def _apply_sort_to_specimens(self, sort_by, specimens):

        if sort_by is None:
            specimens = specimens.sort_values(by=['added_to_curation'], ascending=[False])
        else:
            if sort_by.startswith('-'):
                column_name = sort_by[1:]
                sort_direction = False
            else:
                column_name = sort_by
                sort_direction = True

            specimens = specimens.sort_values(by=[column_name, 'added_to_curation'],
                                              ascending=[sort_direction, False])

        return specimens

    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        page_size: int = None,
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:

        query = self._build_jira_query()
        response = self._execute_jira_query(query)

        # Convert raw jira output data to visible outputs.
        specimens = self._parse_jira_output(response)

        # object_filters needs to be dict - currently string
        object_filters_dict = json.loads(object_filters)

        # Filter
        if object_filters_dict and len(object_filters_dict.keys()) > 0:

            if 'contains' in object_filters_dict.keys():
                specimens = self._apply_contains_filter_to_specimens(
                    object_filters_dict['contains'], specimens)

            if 'range' in object_filters_dict.keys():
                specimens = self._apply_range_filter_to_specimens(
                    object_filters_dict['range'], specimens)

        # Sort
        specimens = self._apply_sort_to_specimens(sort_by, specimens)

        # specimens = specimens[specimens['jbrowse_url']
        #                         .str.contains('sanger')]

        full_len = len(specimens)

        if not page_size:
            page_size = 50

        if not page:
            page = 1

        end_val = int(page) * int(page_size)
        start_val = end_val - int(page_size)

        if len(specimens) < end_val:
            end_val = len(specimens)

        # Filter to current page
        specimens = specimens.iloc[start_val:end_val, ]

        return (specimens.to_dict('records'), full_len)

    def get_specimens_for_treeval(self, page_number, page_size, filter_, sort_by):

        specimens_page, total_specimen_count = self.get_list_page(
            object_type='specimen',
            page=page_number,
            object_filters=filter_,
            sort_by=sort_by,
            page_size=page_size
        )

        return {'total': total_specimen_count, 'data': specimens_page}

    def get_specimen_for_treeval(self, tolid):
        return self.get_specimens_for_treeval(1, 1, f'[tolid={tolid}]', 'tolid')[0]

    def get_by_id():
        raise NotImplementedError()

    def get_list():
        raise NotImplementedError()

    def get_aggregations():
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    @cache
    def supported_types(self):
        raise NotImplementedError()
