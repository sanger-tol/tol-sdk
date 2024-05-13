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
        attributes = {
            'projectcode':
                data_object.sts_gal_abbreviation
                if data_object.sts_gal_abbreviation is not None else '',
            'sampleid':
                data_object.sts_specimen.id
                if data_object.sts_specimen is not None else '',
            'fieldid': '',
            'institutionstoring': 'Wellcome Sanger Institute',
            'phylum': 'Arthropoda',
            'class': '',
            'order': '',
            'extrainfo': loc,
            'notes': '',
            'voucherstatus': '',
            'tissuedescriptor':
                ' | '.join(data_object.sts_organism_part)
                if data_object.sts_organism_part is not None else '',
            'collectors': self.__extract_names_from_contributors(data_object.sts_CONTRIBUTORS),
            'collectiondate':
                data_object.sts_col_date.strftime('%Y-%m-%d')
                if data_object.sts_col_date is not None else '',
            'countryocean':
                data_object.sts_COUNTRY_OF_COLLECTION.title()
                if data_object.sts_COUNTRY_OF_COLLECTION is not None else '',
            'stateprovince': '',
            'lat':
                data_object.sts_latitude
                if data_object.sts_latitude is not None else '',
            'lon':
                data_object.sts_longitude
                if data_object.sts_longitude is not None else '',
            'elev': '',
            'elevationprecision': '',
            'collectiondateaccuarcy': '',
            'samplingprotocol':
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
