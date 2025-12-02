# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict
import re

from tol.core import Validator
from tol.core.data_object import DataObject
from tol.ena.ena_datasource import DataSource 

Config = Dict[str, str]

class UniqueWholeOrganismsValidator(Validator):
    """
    validates the ENA_CHECKLIST for each samples 
    """
    __slots__ = ['__config']
    
    def __init__(self, config: Config) -> None:
        super().__init__()
    
    def __collection_country(self, sample):
        return re.split(r'\s*\|\s*', sample.attributes.get['COLLECTION_LOCATION'])[0]

    def __collection_region(self, sample):
        return ' | '.join(re.split(r'\s*\|\s*', sample.attributes.get['COLLECTION_LOCATION'])[1:])

    def __replace_underscores(self, value):
        if type(value) != str:
            return value
        return self.__sanitise(value, '').replace('_', ' ')

    def __sanitise(self, value, default_value=''):
        if value is None:
            return default_value
        return value

    def __convert_sample_to_ena_format(self, sample):
        # Listed in the order they appear on the ENA checklist
        print(sample)
        ret = {'ENA-CHECKLIST': {'value': 'ERC000053'}}
        ret['organism part'] = {'value': self.__replace_underscores(sample.attributes.get['ORGANISM_PART'])}
        ret['lifestage'] = {
            'value': 'spore-bearing structure' if sample.attributes.get['LIFESTAGE'] == 'SPORE_BEARING_STRUCTURE'
            else self.__replace_underscores(sample.attributes.get['LIFESTAGE'])}
        ret['project name'] = {'value': self._project_name}
        ret['collected by'] = {'value': self.__replace_underscores(sample.attributes.get['COLLECTED_BY'])}
        ret['collection date'] = {'value': self.__replace_underscores(sample.attributes.get['DATE_OF_COLLECTION']).lower()}  # noqa
        ret['geographic location (country and/or sea)'] = {
            'value': self.__collection_country(sample).replace('_', ' ')}
        ret['geographic location (latitude)'] = {'value': self.__replace_underscores(sample.attributes.get['DECIMAL_LATITUDE']).lower(),  # noqa
                                                 'units': 'DD'}
        ret['geographic location (longitude)'] = {'value': self.__replace_underscores(sample.attributes.get['DECIMAL_LONGITUDE']).lower(),  # noqa
                                                  'units': 'DD'}
        ret['geographic location (region and locality)'] = {
            'value': self.__collection_region(sample).replace('_', ' ')}
        ret['identified_by'] = {'value': self.__replace_underscores(sample.attributes.get['IDENTIFIED_BY'])}
        if self.__sanitise(sample.attributes.get['DEPTH']) != '':
            ret['geographic location (depth)'] = {'value': sample.attributes.get['DEPTH'],
                                                  'units': 'm'}
        if self.__sanitise(sample.attributes.get['ELEVATION']) != '':
            ret['geographic location (elevation)'] = {'value': sample.attributes.get['ELEVATION'],
                                                      'units': 'm'}
        ret['habitat'] = {'value': self.__replace_underscores(sample.attributes.get['HABITAT'])}
        ret['identifier_affiliation'] = \
            {'value': self.__replace_underscores(sample.attributes.get['IDENTIFIER_AFFILIATION'])}
        if self.__sanitise(sample.attributes.get['ORIGINAL_COLLECTION_DATE']) != '':
            ret['original collection date'] = {'value': sample.attributes.get['ORIGINAL_COLLECTION_DATE']}
        if self.__sanitise(sample.attributes.get['ORIGINAL_GEOGRAPHIC_LOCATION']) != '':
            ret['original geographic location'] = {'value': self.__replace_underscores(sample.attributes.get['ORIGINAL_GEOGRAPHIC_LOCATION'])}  # noqa
        ret['sex'] = {'value': self.__replace_underscores(sample.attributes.get['SEX'])}
        ret['relationship'] = {'value': self.__replace_underscores(sample.attributes.get['RELATIONSHIP'])}
        ret['symbiont'] = {'value': 'Y' if sample.attributes.get['SYMBIONT'] == 'SYMBIONT' else 'N'}
        ret['collecting institution'] = \
            {'value': self.__replace_underscores(sample.attributes.get['COLLECTOR_AFFILIATION'])}
        if sample.attributes.get['GAL'] is not None:
            ret['GAL'] = {'value': sample.attributes.get['GAL']}
        if sample.attributes.get['VOUCHER_ID'] is not None:
            ret['specimen_voucher'] = {'value': sample.attributes.get['VOUCHER_ID']}
        if sample.attributes.get['SPECIMEN_ID'] is not None:
            ret['specimen_id'] = {'value': sample.attributes.get['SPECIMEN_ID']}
        if sample.attributes.get['GAL_SAMPLE_ID'] is not None:
            ret['GAL_sample_id'] = {'value': sample.attributes.get['GAL_SAMPLE_ID']}
        if sample.attributes.get['CULTURE_OR_STRAIN_ID'] is not None:
            ret['culture_or_strain_id'] = {'value': sample.attributes.get['CULTURE_OR_STRAIN_ID']}
        return ret

    
    def _validate_data_object(self, obj: DataObject) -> None:
        ena_checklist = DataSource.get_by_id("checklist", ['ERC000053', 'ERC000036'])
        ena_fields = self.__convert_sample_to_ena_format(obj)
        for check in ena_checklist:
            field_name = check
            if 'field' in ena_checklist[check]:
                ena