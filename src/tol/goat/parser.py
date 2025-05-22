# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


GoatApiResource = dict[str, Any]
GoatApiDoc = dict[str, list[GoatApiResource]]


class Parser(ABC):
    """
    Parses GoaT API transfer resource `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[GoatApiResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of GoaT API transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: GoatApiResource) -> DataObject:
        """
        Parses an individual GoaT transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):

    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(self, transfer: GoatApiResource) -> DataObject:
        type_ = 'taxon'
        ds = self.__get_data_source(type_)
        raw_attributes = transfer.get('result')
        attributes = self.__convert_attributes(type_, raw_attributes)

        return ds.data_object_factory(
            type_,
            id_=transfer.get('result').get('taxon_id'),
            attributes=attributes,
            to_one=self.__parse_to_ones(transfer)
        )

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__dict[type_]

    def __convert_attributes(
            self,
            type_: str,
            attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        ret = {}
        if attributes is None:
            return ret
        # Direct attributes
        for att in ['scientific_name', 'taxon_rank']:
            ret[att] = attributes.get(att)

        # Attributes with values in fields
        normal_fields = [
            'genome_size', 'chromosome_number',
            'haploid_number', 'ploidy', 'assembly_level'
        ]
        one_or_list_fields = ['echabs92', 'habreg_2017', 'marhabreg-2017', 'waca_1981',
                              'isb_wildlife_act_1976', 'protection_of_badgers_act_1992',
                              'family_representative', 'long_list', 'sample_collected']
        if 'fields' in attributes:
            for att in normal_fields + one_or_list_fields:
                if att in attributes['fields']:
                    att_value = attributes['fields'][att]
                    if att_value is not None and 'value' in att_value:
                        if att in one_or_list_fields and \
                                not isinstance(att_value['value'], list):
                            ret[att] = [att_value['value']]
                        else:
                            ret[att] = att_value['value']
        if 'names' in attributes:
            for att in attributes['names']:
                if att == 'synonym':
                    synonym_value = attributes['names'][att]['name']
                    if isinstance(synonym_value, list):
                        ret[att] = synonym_value
                    else:
                        ret[att] = [synonym_value]
                else:
                    ret[att] = attributes['names'][att]['name'][0]

        # Lineage
        if 'ranks' in attributes:
            ret['lineage'] = []
            for _, ancestor in attributes['ranks'].items():
                ret['lineage'] = [ancestor['scientific_name']] + ret['lineage']

        return ret

    def __parse_to_ones(
        self,
        transfer: GoatApiResource
    ) -> dict[str, DataObject]:
        raw_attributes = transfer.get('result')
        return {
            k: self.parse({'result': v})
            for k, v in raw_attributes.get('ranks', {}).items()
        }
