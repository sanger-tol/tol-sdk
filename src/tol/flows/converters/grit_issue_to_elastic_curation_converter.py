# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectFactory,
    DataObjectToDataObjectOrUpdateConverter
)


class GritIssueToElasticCurationConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['_data_object_factory']
    _data_object_factory: DataObjectFactory

    ATTRIBUTES_PARSED_SEPARATELY = ('assembly_statistics', 'chromosome_result', 'status_changes')
    ATTRIBUTES_IGNORED = ('description', 'tolid', 'linked_issues')

    def __init__(self, data_object_factory: DataObjectFactory, config: Config) -> None:
        super().__init__(data_object_factory)
        self._data_object_factory = data_object_factory

        # No config needed for this converter
        del config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.assembled_by in (
            'Blaxter',
            'Jaron Group',
            'ToL',
            'Lawniczak'
        ):
            # Parse the fields in ATTRIBUTES_PARSED_SEPARATELY
            assembly_stats = self.__get_assembly_stats(
                data_object.attributes.get('assembly_statistics')
            )
            chr_data = self.__get_chr_data(data_object.attributes.get('chromosome_result'))
            assert data_object.status_changes is not None
            status_changes = {
                self.__sanitise_attribute_name(sc['next_status']) + '_date': sc['end_date']
                for sc in data_object.status_changes
            }
            optional_attributes = {
                'assignee_name': data_object.assignee.name if data_object.assignee else None
            }

            # The rest of the attributes are just copied across from the input data object
            unchanged_attributes = {
                key: value for key, value in data_object.attributes.items()
                if key not in self.ATTRIBUTES_PARSED_SEPARATELY + self.ATTRIBUTES_IGNORED
            }

            # Combine all of these to form the attributes dict
            attributes = assembly_stats | chr_data | status_changes | optional_attributes | unchanged_attributes

            to_one_relations = {
                'tolid': self._data_object_factory(
                    'tolid',
                    data_object.attributes.get('tolid')
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
