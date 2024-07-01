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
        length_info = self.__get_length_info(data_object.attributes.get('assembly_statistics'))
        n50_info = self.__get_n50_info(data_object.attributes.get('assembly_statistics'))
        scaff_count_info = \
            self.__get_scaff_count(data_object.attributes.get('assembly_statistics'))
        chr_data = self.__get_chr_data(data_object.attributes.get('chromosome_result'))
        attributes = {
            k: v for k, v in data_object.attributes.items()
            if k not in ['assembly_statistics', 'chromosome_result', 'description',
                         'sample_id', 'status_changes', 'linked_issues']
        } | {
            self.__sanitise_attribute_name(sc['next_status']) + '_date': sc['end_date']
            for sc in data_object.status_changes
        } | length_info | n50_info | scaff_count_info | chr_data

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

    def __get_length_info(self, data):
        """
        Function to return the length information hidden in assembly stats
        :param scaff_data:
        :return:
        """
        if data:
            length_search = re.search(r'total\s*([0-9]\w+)\s*([0-9]\w+)', data)
            length_before = int(length_search.group(1))
            length_after = int(length_search.group(2))
            length_change_per = (length_after - length_before) / length_before * 100
            return {
                'length_before': length_before,
                'length_after': length_after,
                'length_change_per': length_change_per
            }
        else:
            return {}

    def __get_n50_info(self, scaff_data):
        """
        Function to return the length information hidden in assembly stats
        :param scaff_data:
        :return:
        """
        if scaff_data:
            n50_search = re.search(r'N50\s*([0-9]*)\s*([0-9]*)', scaff_data)
            n50_before = int(n50_search.group(1))
            n50_after = int(n50_search.group(2))
            n50_ab = n50_after - n50_before
            if n50_ab == 0:
                n50_change_per = 0
            else:
                n50_change_per = (n50_after - n50_before) / n50_before * 100
            return {
                'n50_before': n50_before,
                'n50_after': n50_after,
                'n50_change_per': n50_change_per
            }
        else:
            return {}

    def __get_scaff_count(self, scaff_data):
        """

        :param scaff_data:
        :return:
        """
        if scaff_data:
            scaff_count_search = re.search(r'count\s*([0-9]*)\s*([0-9]*)', scaff_data)
            scaff_count_before = int(scaff_count_search.group(1))
            scaff_count_after = int(scaff_count_search.group(2))
            if scaff_count_before + scaff_count_after == 0:
                scaff_count_per = 0
            else:
                scaff_count_per = (
                    (scaff_count_after - scaff_count_before) / scaff_count_before * 100
                )
            return {
                'scaff_count_before': scaff_count_before,
                'scaff_count_after': scaff_count_after,
                'scaff_count_per': scaff_count_per
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
