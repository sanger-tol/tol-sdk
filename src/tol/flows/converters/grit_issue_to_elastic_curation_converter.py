# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

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

    ATTRIBUTES_PARSED_SEPARATELY = (
        'assembly_statistics', 'chromosome_result', 'status_changes'
    )
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
            treeval_data = self.__get_treeval_data(data_object)
            treeval_links = self.__get_treeval_links(data_object, treeval_data)
            contamination_data = (
                self.__get_contamination_data(data_object.contamination)
                if data_object.contamination is not None
                else {}
            )
            status_changes = (
                {
                    self.__sanitise_attribute_name(sc['next_status']) + '_date': sc['end_date']
                    for sc in data_object.status_changes
                }
                if data_object.status_changes is not None
                else {}
            )
            optional_attributes = {
                'assignee_name': data_object.assignee.name if data_object.assignee else None
            }

            # The rest of the attributes are just copied across from the input data object
            unchanged_attributes = {
                key: value for key, value in data_object.attributes.items()
                if key not in self.ATTRIBUTES_PARSED_SEPARATELY + self.ATTRIBUTES_IGNORED
            }

            # Combine all of these to form the attributes dict
            attributes = (
                assembly_stats | chr_data
                | treeval_data | treeval_links
                | contamination_data | status_changes
                | optional_attributes | unchanged_attributes
            )

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

    def __get_treeval_data(self, data_object: DataObject) -> dict[str, Any]:
        """
        Function to parse the fields out from the `treeval_data` and `treeval` attributes
        """
        treeval_data_dict = json.loads(data_object.treeval_data or str({}))

        # Extract each key-value pair from the `treeval_data` dict attribute,
        # and give them the 'treeval_' prefix
        extracted_treeval_data = (
            {f'treeval_{key}': value for key, value in treeval_data_dict.items()}
            if data_object.treeval_data is not None
            else {}
        )

        # Parse the `treeval` attribute
        treeval_attribute = data_object.treeval or ''
        hap1_match = re.search(r'hap1: ([a-zA-Z]*[0-9]*_[a-zA-Z0-9-]*)', treeval_attribute)
        hap2_match = re.search(r'hap2: ([a-zA-Z]*[0-9]*_[a-zA-Z0-9-]*)', treeval_attribute)
        merged_match = re.search(r'merged: ([a-zA-Z]*[0-9]*_[a-zA-Z0-9-]*)', treeval_attribute)
        analyses = {
            'treeval_hap1_analysis': hap1_match.group(1) if hap1_match is not None else None,
            'treeval_hap2_analysis': hap2_match.group(1) if hap2_match is not None else None,
            'treeval_merged_analysis': merged_match.group(1) if merged_match is not None else None,
        }

        # Combine the two into one dict
        return extracted_treeval_data | analyses

    def __get_treeval_links(
        self,
        data_object: DataObject,
        treeval_data: dict[str, Any]
    ) -> dict[str, str | None]:
        """
        Function to parse the fields
        `treeval_hic_map_link`, `treeval_kmer_spectra_link` and `treeval_jbrowse_link`
        from the data object, using values in the already parsed `treeval_data` dict
        """
        # The image links should use the Merged analysis if we're combining for curation,
        # else use the Hap1 analysis
        treeval_labels = data_object.labels or []
        preferred_analysis = treeval_data[
            'treeval_merged_analysis'
            if 'combine_for_curation' in treeval_labels
            else 'treeval_hap1_analysis'
        ]

        # Extract the attributes needed to build the jbrowse link
        jbrowse = treeval_data.get('treeval_jbrowse')
        jbrowse_server_url = 'tol-dev' if treeval_data.get('treeval_jb_server') == 'dev' else 'tol'
        # `or` is used here instead of a default in `get` because it should be a default
        # for an empty string as well
        jbrowse_scaffold = treeval_data.get('treeval_jb_scaffold') or 'SCAFFOLD_1'

        return {
            'treeval_hic_map_link': (
                f'https://treeval.cog.sanger.ac.uk/pretextsnapshot_{preferred_analysis}.png'
            ),
            'treeval_kmer_spectra_link': (
                f'https://treeval.cog.sanger.ac.uk/kmerspectra_{preferred_analysis}.png'
            ),
            'treeval_jbrowse_link': (
                r'http://jbrowse.' + jbrowse_server_url + r'.sanger.ac.uk/jbrowse2/'
                + r'?config=config.json&assembly=' + jbrowse + r'&session=spec-{%22views%22:[{'
                + r'%22assembly%22:%22' + jbrowse + r'%22,%22loc%22:%22' + jbrowse_scaffold
                + r'%22,%22type%22:%22LinearGenomeView%22,%22tracks%22:[%22' + jbrowse
                + r'-ReferenceSequenceTrack%22]}]}'
            ) if jbrowse else None
        }

    def __get_contamination_data(
        self, contamination_attribute: str
    ) -> dict[str, float | None | bool]:
        """
        Function to parse the fields
        `total_removed`, `total_removed_percent`, `count_removed`, `count_removed_percent`,
        `largest_removed` and `is_abnormal`
        from the `contamination` attribute of the input data object (which is a big block of text)
        """
        def __extract_group(match: re.Match | None, group: int) -> float | None:
            """
            Shortcut function to extract the contents of a capturing group as an int
            from a regex match, or None if no matches were found
            """
            if not match:
                return None
            value_as_string: str = match.group(group)
            return float(value_as_string.replace(',', ''))

        match_total_removed = re.search(
            r'Total length of scaffolds removed: ([0-9,]+) \(([0-9\.]+) %\)',
            contamination_attribute
        )
        match_count_removed = re.search(
            r'Scaffolds removed: ([0-9,]+) \(([0-9\.]+) %\)',
            contamination_attribute
        )
        match_largest_removed = re.search(
            r'Largest scaffold removed: \(([0-9,]+)\)',
            contamination_attribute
        )

        return {
            'contamination_total_removed': __extract_group(match_total_removed, 1),
            'contamination_total_removed_percent': __extract_group(match_total_removed, 2),
            'contamination_count_removed': __extract_group(match_count_removed, 1),
            'contamination_count_removed_percent': __extract_group(match_count_removed, 2),
            'contamination_largest_removed': __extract_group(match_largest_removed, 1),
            'contamination_is_abnormal': 'Abnormal contamination report' in contamination_attribute
        }
