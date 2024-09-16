# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GritIssueToElasticCurationConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        assembly_stats = self.__get_assembly_stats(
            data_object.attributes.get('assembly_statistics')
        )
        chr_data = self.__get_chr_data(data_object.attributes.get('chromosome_result'))
        attributes = {
            k: v for k, v in data_object.attributes.items()
            if k not in ['assembly_statistics', 'chromosome_result', 'description',
                         'sample_id', 'status_changes', 'linked_issues']
        } | {
            self.__sanitise_attribute_name(sc['next_status']) + '_date': sc['end_date']
            for sc in data_object.status_changes
        } | {
            'assignee_name': data_object.assignee.name if data_object.assignee else None,
        } | assembly_stats | chr_data

        to_one_relations = {
            'tolid': self._data_object_factory(
                'tolid',
                data_object.attributes.get('sample_id')
            )
        }
        ret = self._data_object_factory(
            'curation',
            data_object.id,
            attributes=attributes,
            to_one=to_one_relations
        )
        yield ret

    def __sanitise_attribute_name(self, name: str) -> str:
        return re.sub(r'\s+', '_', name.lower())

    def __get_assembly_stats(self, data):
        if not data:
            return {}
        assembly_stats = {}
        pattern = re.compile(
            r'(?P<section>scaffolds|contigs)\n(?P<section_data>'
            r'(?:[a-zA-Z0-9]+\s+\d+\s+\d+\s*\n?)+)'
        )
        for match in pattern.finditer(data):
            section = match.group('section')
            section_data = match.group('section_data')
            for att in ['total', 'count', 'N50', 'L50', 'N90', 'L90']:
                assembly_stats.update(self.__get_assembly_info(section_data, section, att))
        return assembly_stats

    def __get_assembly_info(self, data, contig_or_scaffold, att):
        """
        Function to return the information hidden in assembly stats
        """
        if data:
            att_search = re.search(rf'{att}\s*([0-9]\w*)\s*([0-9]\w*)', data)
            att_before = int(att_search.group(1))
            att_after = int(att_search.group(2))
            att_change_per = (att_after - att_before) / att_before * 100
            return {
                f'{contig_or_scaffold}_{att.lower()}_before': att_before,
                f'{contig_or_scaffold}_{att.lower()}_after': att_after,
                f'{contig_or_scaffold}_{att.lower()}_change_per': att_change_per
            }
        else:
            return {}

    def __get_chr_data(self, chromo_res):
        """
        Function to parse and return the chromosome assignment and assignment %
        :param chromo_res:
        :return:
        """
        if chromo_res:
            chr_ass_search = re.search(r'(found.[0-9].*somes.*\(.*\))', chromo_res)
            if chr_ass_search:
                chr_ass = chr_ass_search.group(1)
            elif chr_ass_search is None:
                chr_ass_search = re.search(r'(found.[0-9].*somes)', chromo_res)
                if chr_ass_search:
                    chr_ass = chr_ass_search.group(1)
                else:
                    chr_ass = None
            else:
                chr_ass = None

            ass_percent_search = re.search(r'Chr.length.(\d*.\d*).%', chromo_res)
            ass_percent = ass_percent_search.group(1) if ass_percent_search else None
            return {
                'chr_ass': chr_ass,
                'ass_percent': ass_percent
            }
        else:
            return {}
