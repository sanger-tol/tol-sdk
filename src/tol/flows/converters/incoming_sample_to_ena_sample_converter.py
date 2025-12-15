# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class IncomingSampleToEnaSampleConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        ena_checklist_id: str
        project_name: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        converting the samples DataObject into ENA format
        """
        s = data_object
        attributes = {
            'ENA-CHECKLIST': self.__config.ena_checklist_id,
            'organism part': self.__join_list([
                self.__replace_underscores(v)
                for v in s.attributes.get('ORGANISM_PART', [])
            ]),
            'lifestage': (
                'spore-bearing structure'
                if s.attributes.get('LIFESTAGE') == 'SPORE_BEARING_STRUCTURE'
                else self.__replace_underscores(
                    s.attributes.get('LIFESTAGE'))
            ),
            'project name':
                self.__config.project_name,
            'collected_by': self.__join_list([
                self.__replace_underscores(v)
                for v in s.attributes.get('COLLECTED_BY', [])
            ]),
            'collection date':
                self.__format_date(
                    s.attributes.get('DATE_OF_COLLECTION')),
            'geographic location (country and/or sea)':
                self.__collection_country(s).replace('_', ' '),
            'geographic location (latitude)':
                self.__replace_underscores(
                    str(s.attributes.get('DECIMAL_LATITUDE'))).lower(),
            'geographic location (latitude) units':
                'DD',
            'geographic location (longitude)':
                self.__replace_underscores(
                    str(s.attributes.get('DECIMAL_LONGITUDE'))).lower(),
            'geographic location (longitude) units':
                'DD',
            'geographic location (region and locality)':
                self.__collection_region(s).replace('_', ' '),
            'identified_by': self.__join_list([
                self.__replace_underscores(v)
                for v in s.attributes.get('IDENTIFIED_BY', [])
            ]),
            'habitat':
                self.__replace_underscores(
                    s.attributes.get('HABITAT')),
            'identifier_affiliation': self.__join_list([
                self.__replace_underscores(v)
                for v in s.attributes.get('IDENTIFIER_AFFILIATION', [])
            ]),
            'sex':
                self.__replace_underscores(
                    s.attributes.get('SEX')),
            'relationship':
                self.__replace_underscores(
                    s.attributes.get('RELATIONSHIP')),
            'SYMBIONT':
                'Y' if s.attributes.get('SYMBIONT') == 'SYMBIONT' else 'N',
            'collecting institution': self.__join_list([
                self.__replace_underscores(v)
                for v in s.attributes.get('COLLECTOR_AFFILIATION', [])
            ]),
        }
        if self.__sanitise(s.attributes.get('DEPTH')) != '':
            attributes['geographic location (depth)'] = s.attributes.get('DEPTH')
            attributes['geographic location (depth) units'] = 'm'
        if self.__sanitise(s.attributes.get('ELEVATION')) != '':
            attributes['geographic location (elevation)'] = s.attributes.get('ELEVATION')
            attributes['geographic location (elevation) units'] = 'm'
        if self.__sanitise(s.attributes.get('ORIGINAL_COLLECTION_DATE')) != '':
            attributes['original collection date'] = \
                self.__format_date(s.attributes.get('ORIGINAL_COLLECTION_DATE'))
        if self.__sanitise(s.attributes.get('ORIGINAL_GEOGRAPHIC_LOCATION')) != '':
            attributes['original geographic location'] = \
                self.__replace_underscores(s.attributes.get('ORIGINAL_GEOGRAPHIC_LOCATION'))
        if s.attributes.get('GAL') is not None:
            attributes['GAL'] = s.attributes.get('GAL')
        if s.attributes.get('VOUCHER_ID') is not None:
            attributes['specimen_voucher'] = s.attributes.get('VOUCHER_ID')
        if s.attributes.get('SPECIMEN_ID') is not None:
            attributes['specimen_id'] = s.attributes.get('SPECIMEN_ID')
        if s.attributes.get('GAL_SAMPLE_ID') is not None:
            attributes['GAL_sample_id'] = s.attributes.get('GAL_SAMPLE_ID')
        if s.attributes.get('CULTURE_OR_STRAIN_ID') is not None:
            attributes['culture_or_strain_id'] = s.attributes.get('CULTURE_OR_STRAIN_ID')

        ret = self._data_object_factory(
            data_object.type,
            s.id,
            attributes=attributes,
        )
        yield ret

    def __collection_country(self, data_object: DataObject):
        return re.split(
            r'\s*\|\s*',
            data_object.attributes.get('COLLECTION_LOCATION'))[0]

    def __collection_region(self, data_object: DataObject):
        return ' | '.join(re.split(
            r'\s*\|\s*',
            data_object.attributes.get('COLLECTION_LOCATION'))[1:])

    def __replace_underscores(self, value):
        if type(value) != str:
            return value
        return self.__sanitise(value, '').replace('_', ' ')

    def __sanitise(self, value, default_value=''):
        if value is None:
            return default_value
        return value

    def __join_list(self, value_list):
        if value_list is None:
            return ''
        if not isinstance(value_list, list):
            return str(value_list)
        return ' | '.join(str(v) for v in value_list)

    def __format_date(self, value):
        """Format date to YYYY-mm-dd format"""
        if value is None:
            return ''
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')

        return str(value)
