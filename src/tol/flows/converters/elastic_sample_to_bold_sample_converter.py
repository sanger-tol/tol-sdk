# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import (
    Iterable
)

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToBoldSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        loc = f'{data_object.sts_gal_name} - {data_object.sts_gal_abbreviation}'
        if len(loc) == 51:
            loc = f'{data_object.sts_gal_name}- {data_object.sts_gal_abbreviation}'
        if len(loc) > 50:
            loc = 'dummy'
        if data_object.sts_gal_name is None:
            loc = ''
        if data_object.sts_rackid is not None:
            project_code = data_object.sts_rackid.split('_')[0]
        else:
            project_code = ''
        upd_codes = {
            'NHMG': 'BNHMG',
            'CARM': 'BCARM',
            'CAMP': 'SCAMP',
            'EWTA': 'BEWTA',
            'NTDB': 'BNTDB',
            'FMED': 'BFMED'
        }
        if project_code in upd_codes.keys():
            project_code = upd_codes[project_code]
        attributes = {
            'bold_recordset_code_arr': project_code,
            'sampleid':
                data_object.sts_specimen.id
                if data_object.sts_specimen is not None else '',
            'fieldid': '',
            'inst': 'Wellcome Sanger Institute',
            'phylum': 'Arthropoda',
            'class': '',
            'order': '',
            'short_note': loc,
            'notes': '',
            'voucher_type': '',
            'tissue_type':
                ' | '.join(data_object.sts_organism_part)
                if data_object.sts_organism_part is not None else '',
            'collectors': self.__extract_names_from_contributors(data_object.sts_CONTRIBUTORS),
            'collection_date_start':
                data_object.sts_col_date.strftime('%Y-%m-%d')
                if data_object.sts_col_date is not None else '',
            'country/ocean':
                data_object.sts_COUNTRY_OF_COLLECTION.title()
                if data_object.sts_COUNTRY_OF_COLLECTION is not None else '',
            'province/state': '',
            'coord':
                f'{data_object.sts_latitude},{data_object.sts_longitude}'
                if data_object.sts_latitude is not None
                and data_object.sts_longitude is not None else '',
            'elev': '',
            'elev_accuracy': '',
            'collection_date_end': '',
            'sampling_protocol':
                data_object.sts_COLLECTION_METHOD.replace('_', ' ').title()
                if data_object.sts_COLLECTION_METHOD is not None else '',
        }
        ret = self._data_object_factory(
            'sample',
            data_object.id,
            attributes=attributes
        )
        yield ret

    def __extract_names_from_contributors(self, contributors: str) -> str:
        try:
            c_list = contributors.split('|')
        except AttributeError:
            c_list = ''
        names = [c.split(';')[0] for c in c_list]
        return ', '.join(names)
