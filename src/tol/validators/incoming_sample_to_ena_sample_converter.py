from typing import Iterable
from core import DataObject, DataObjectToDataObjectOrUpdateConverter

class IncomingSampleToEnaSampleConverter(DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        converting the samples DataObject into ENA format
        """
        sample = data_object
        attributes = {
            'ENA-CHECKLIST': 'ERC000053',
            'organism part': self.__replace_underscores(sample.attributes.get('ORGANISM_PART')),
            'lifestage': (
                'spore-bearing structure' if sample.attributes.get('LIFESTAGE') == 'SPORE_BEARING_STRUCTURE'
                else self.__replace_underscores(sample.attributes.get('LIFESTAGE'))
            ),
            # 'project name': self._project_name 
            'collected by': self.__replace_underscores(sample.attributes.get('COLLECTED_BY')),
            'collection date': self.__replace_underscores(sample.attributes.get('DATE_OF_COLLECTION')).lower(),
            'geographic location (country and/or sea)': self.__collection_country(sample).replace('_', ' '),
            'geographic location (latitude)': self.__replace_underscores(sample.attributes.get('DECIMAL_LATITUDE')).lower(),
            'geographic location (latitude) units': 'DD',
            'geographic location (longitude)': self.__replace_underscores(sample.attributes.get('DECIMAL_LONGITUDE')).lower(),
            'geographic location (longitude) units': 'DD',
            'geographic location (region and locality)': self.__collection_region(sample).replace('_', ' '),
            'identified_by': self.__replace_underscores(sample.attributes.get('IDENTIFIED_BY')),
            'habitat': self.__replace_underscores(sample.attributes.get('HABITAT')),
            'identifier_affiliation': self.__replace_underscores(sample.attributes.get('IDENTIFIER_AFFILIATION')),
            'sex': self.__replace_underscores(sample.attributes.get('SEX')),
            'relationship': self.__replace_underscores(sample.attributes.get('RELATIONSHIP')),
            'SYMBIONT': 'Y' if sample.attributes.get['SYMBIONT'] == 'SYMBIONT' else 'N',
            'collecting institution': self.__replace_underscores(sample.attributes.get('COLLECTOR_AFFILIATION'))
        }
        if self.__sanitise(sample.attributes.get('DEPTH')) != '':
            attributes['geographic location (depth)'] = sample.attributes.get('DEPTH')
            attributes['geographic location (depth) units'] = 'm'
        if self.__sanitise(sample.attributes.get('ELEVATION')) != '':
            attributes['geographic location (elevation)'] = sample.attributes.get('ELEVATION')
            attributes['geographic location (elevation) units'] = 'm'
        if self.__sanitise(sample.attributes.get('ORIGINAL_COLLECTION_DATE')) != '':
            attributes['original collection date'] = sample.attributes.get('ORIGINAL_COLLECTION_DATE')
        if self.__sanitise(sample.attributes.get('ORIGINAL_GEOGRAPHIC_LOCATION')) != '':
            attributes['original geographic location'] = self.__replace_underscores(sample.attributes.get('ORIGINAL_GEOGRAPHIC_LOCATION'))  # noqa
        if sample.attributes.get('GAL') is not None:
            attributes['GAL'] = sample.attributes.get('GAL')
        if sample.attributes.get('VOUCHER_ID') is not None:
            attributes['specimen_voucher'] = sample.attributes.get('VOUCHER_ID')
        if sample.attributes.get('SPECIMEN_ID') is not None:
            attributes['specimen_id'] = sample.attributes.get('SPECIMEN_ID')
        if sample.attributes.get('GAL_SAMPLE_ID') is not None:
            attributes['GAL_sample_id'] = sample.attributes.get('GAL_SAMPLE_ID')
        if sample.attributes.get('CULTURE_OR_STRAIN_ID') is not None:
            attributes['culture_or_strain_id'] = sample.attributes.get('CULTURE_OR_STRAIN_ID')

        to_one = {}

        ret = self._data_object_factory(
            'sample',
            sample.id,
            attributes=attributes,
            to_one=to_one
        )
        yield ret
