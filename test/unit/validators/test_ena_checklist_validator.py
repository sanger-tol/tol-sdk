# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
from typing import Any

from tol.core import DataObject, DataSource, core_data_object
from tol.flows.converters import IncomingSampleToEnaSampleConverter
from tol.validators import EnaChecklistValidator


class MockEnaDataSource(DataSource):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config, [])

    @property
    def supported_types(self) -> list[str]:
        return ['checklist']

    def get_one(self, type_, id_):
        return self.data_object_factory(
            'checklist',
            'ERC123456',
            attributes={
                'checklist': {
                    'Latitude Start': [
                        'optional',
                        'restricted text',
                        r'[+-]?[0-9]+.?[0-9]*',
                    ],
                    'Longitude Start': [
                        'optional',
                        'restricted text',
                        r'[+-]?[0-9]+.?[0-9]*',
                    ],
                    'Latitude End': [
                        'optional',
                        'restricted text',
                        r'[+-]?[0-9]+.?[0-9]*',
                    ],
                    'Longitude End': [
                        'optional',
                        'restricted text',
                        r'[+-]?[0-9]+.?[0-9]*',
                    ],
                    'organism part': ['mandatory', 'free text', ''],
                    'lifestage': [
                        'mandatory',
                        'text choice',
                        [
                            'adult',
                            'egg',
                            'embryo',
                            'gametophyte',
                            'juvenile',
                            'larva',
                            'missing: control sample',
                            'missing: data agreement established pre-2023',
                            'missing: endangered species',
                            'missing: human-identifiable',
                            'missing: lab stock',
                            'missing: sample group',
                            'missing: synthetic construct',
                            'missing: third party data',
                            'not applicable',
                            'not collected',
                            'not provided',
                            'pupa',
                            'spore-bearing structure',
                            'sporophyte',
                            'vegetative cell',
                            'vegetative structure',
                            'zygote',
                        ],
                    ],
                    'relationship': ['optional', 'free text', ''],
                    'sample symbiont of': [
                        'optional',
                        'restricted text',
                        r'(^[ESD]RS\d{6,}$)|(^SAM[END][AG]?\d+$)|(^EGAN\d{11}$)',
                    ],
                    'symbiont': ['optional', 'text choice', ['N', 'Y']],
                    'sample collection method': ['optional', 'free text', ''],
                    'sample coordinator affiliation': ['optional', 'free text', ''],
                    'sample same as': [
                        'optional',
                        'restricted text',
                        r'(^[ESD]RS\d{6,}(,[ESD]RS\d{6,})*$)|'
                        r'(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|'
                        r'(^EGAN\d{11}(,EGAN\d{11})*$)',
                    ],
                    'sample derived from': [
                        'optional',
                        'restricted text',
                        r'(^[ESD]R[SR]\d{6,}(,[ESD]R[SR]\d{6,})*$)|'
                        r'(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|'
                        r'(^EGA[NR]\d{11}(,EGA[NR]\d{11})*$)|'
                        r'(^[ESD]R[SR]\d{6,}-[ESD]R[SR]\d{6,}$)|'
                        r'(^SAM[END][AG]?\d+-SAM[END][AG]?\d+$)|'
                        r'(^EGA[NR]\d{11}-EGA[NR]\d{11}$)',
                    ],
                    'project name': ['mandatory', 'free text', ''],
                    'barcoding center': ['optional', 'free text', ''],
                    'tolid': ['optional', 'free text', ''],
                    'collection date': [
                        'mandatory',
                        'restricted text',
                        r'(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])'
                        r'(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?'
                        r'(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}'
                        r'(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|'
                        r'(^not applicable$)|(^not collected$)|(^not provided$)|'
                        r'(^restricted access$)|(^missing: control sample$)|'
                        r'(^missing: sample group$)|(^missing: synthetic construct$)|'
                        r'(^missing: lab stock$)|(^missing: third party data$)|'
                        r'(^missing: data agreement established pre-2023$)|'
                        r'(^missing: endangered species$)|(^missing: human-identifiable$)|'
                        r'(^missing$)',
                    ],
                    'geographic location (latitude)': [
                        'recommended',
                        'restricted text',
                        r'(^[+-]?[0-9]+.?[0-9]{0,8}$)|'
                        r'(^not applicable$)|(^not collected$)|(^not provided$)|'
                        r'(^restricted access$)|(^missing: control sample$)|'
                        r'(^missing: sample group$)|(^missing: synthetic construct$)|'
                        r'(^missing: lab stock$)|(^missing: third party data$)|'
                        r'(^missing: data agreement established pre-2023$)|'
                        r'(^missing: endangered species$)|(^missing: human-identifiable$)|'
                        r'(^missing$)',
                    ],
                    'geographic location (longitude)': [
                        'recommended',
                        'restricted text',
                        r'(^[+-]?[0-9]+.?[0-9]{0,8}$)|'
                        r'(^not applicable$)|(^not collected$)|(^not provided$)|'
                        r'(^restricted access$)|(^missing: control sample$)|'
                        r'(^missing: sample group$)|(^missing: synthetic construct$)|'
                        r'(^missing: lab stock$)|(^missing: third party data$)|'
                        r'(^missing: data agreement established pre-2023$)|'
                        r'(^missing: endangered species$)|(^missing: human-identifiable$)|'
                        r'(^missing$)',
                    ],
                    'geographic location (region and locality)': ['mandatory', 'free text', ''],
                    'identified_by': ['optional', 'free text', ''],
                    'elevation': [
                        'optional',
                        'restricted text',
                        r'([+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?)|'
                        r'((^not applicable$)|(^not collected$)|(^not provided$)|'
                        r'(^restricted access$)|(^missing: control sample$)|'
                        r'(^missing: sample group$)|(^missing: synthetic construct$)|'
                        r'(^missing: lab stock$)|(^missing: third party data$)|'
                        r'(^missing: data agreement established pre-2023$)|'
                        r'(^missing: endangered species$)|(^missing: human-identifiable$)|'
                        r'(^missing$))',
                    ],
                    'habitat': ['mandatory', 'free text', ''],
                    'identifier_affiliation': ['optional', 'free text', ''],
                    'original collection date': [
                        'optional',
                        'restricted text',
                        r'^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])'
                        r'(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?'
                        r'(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}'
                        r'(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$',
                    ],
                    'original geographic location': ['optional', 'free text', ''],
                    'original geographic location (latitude)': [
                        'optional',
                        'restricted text',
                        r'(^[+-]?[0-9]+.?[0-9]{0,8}$)',
                    ],
                    'original geographic location (longitude)': [
                        'optional',
                        'restricted text',
                        r'(^[+-]?[0-9]+.?[0-9]{0,8}$)',
                    ],
                    'sample coordinator': ['optional', 'free text', ''],
                    'sex': ['mandatory', 'free text', ''],
                    'collecting institution': ['mandatory', 'free text', ''],
                    'specimen_id': ['optional', 'free text', ''],
                    'GAL_sample_id': ['optional', 'free text', ''],
                    'proxy voucher': ['optional', 'free text', ''],
                    'proxy biomaterial': ['optional', 'free text', ''],
                    'bio_material': ['optional', 'free text', ''],
                    'specimen_voucher': ['recommended', 'free text', ''],
                    'culture_or_strain_id': ['optional', 'free text', ''],
                    'depth': [
                        'optional',
                        'restricted text',
                        r'((0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?)|'
                        r'((^not applicable$)|(^not collected$)|(^not provided$)|'
                        r'(^restricted access$)|(^missing: control sample$)|'
                        r'(^missing: sample group$)|(^missing: synthetic construct$)|'
                        r'(^missing: lab stock$)|(^missing: third party data$)|'
                        r'(^missing: data agreement established pre-2023$)|'
                        r'(^missing: endangered species$)|(^missing: human-identifiable$)|'
                        r'(^missing$))',
                    ],
                }
            }
        )


class TestEnaChecklistValidator:

    def test_pass(
        self,
        mock_data_source: DataSource
    ) -> None:

        config = EnaChecklistValidator.Config(
            ena_checklist_id='ERC000053',
        )

        converter_config = IncomingSampleToEnaSampleConverter.Config(
            ena_checklist_id='ERC000053',
            project_name='TOL',
        )

        mock_one: DataObject = mock_data_source.data_object_factory(
            'upload',
            'ABC123',
            attributes={
                'ORGANISM_PART': 'WHOLE_ORGANISM',
                'LIFESTAGE': 'ADULT',
                'COLLECTED_BY': 'Dr. Smith',
                'DATE_OF_COLLECTION': '2022-01-01',
                'COLLECTION_LOCATION': 'Country | Region',
                'DECIMAL_LATITUDE': '51.5074',
                'DECIMAL_LONGITUDE': '-0.1278',
                'IDENTIFIED_BY': 'Dr. Jones',
                'HABITAT': 'Forest',
                'IDENTIFIER_AFFILIATION': 'Institute',
                'SEX': 'Male',
                'RELATIONSHIP': 'Parent',
                'SYMBIONT': 'N',
                'COLLECTOR_AFFILIATION': 'Lab',
                'DEPTH': '100',
                'ELEVATION': '200',
                'ORIGINAL_COLLECTION_DATE': '2021-12-31',
                'ORIGINAL_GEOGRAPHIC_LOCATION': 'OldCountry | OldRegion',
                'GAL': 'GAL001',
                'VOUCHER_ID': 'V123',
                'SPECIMEN_ID': 'S123',
                'GAL_SAMPLE_ID': 'GS123',
                'CULTURE_OR_STRAIN_ID': 'CS123'
            }
        )
        converter = IncomingSampleToEnaSampleConverter(
            mock_data_source.data_object_factory,
            converter_config
        )
        result = converter.convert(mock_one)
        mock_ena_datasource = MockEnaDataSource({})
        core_data_object(mock_ena_datasource)
        validator = EnaChecklistValidator(config=config, datasource=mock_ena_datasource)
        list(validator.validate(result))
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 0

    def test_error(
        self,
        mock_data_source: DataSource
    ) -> None:

        config = EnaChecklistValidator.Config(
            ena_checklist_id='ERC000053',
        )

        converter_config = IncomingSampleToEnaSampleConverter.Config(
            ena_checklist_id='ERC000053',
            project_name='TOL',
        )

        mock_one: DataObject = mock_data_source.data_object_factory(
            'upload',
            'ABC123',
            attributes={
                'LIFESTAGE': 'FAIL',
                'COLLECTED_BY': 'Dr. Smith',
                'DATE_OF_COLLECTION': 'XXX-GGG-AAA',
                'COLLECTION_LOCATION': 'Country | Region',
                'DECIMAL_LATITUDE': '51.5074',
                'DECIMAL_LONGITUDE': '-0.1278',
                'IDENTIFIED_BY': 'Dr. Jones',
                'HABITAT': 'Forest',
                'IDENTIFIER_AFFILIATION': 'Institute',
                'SEX': 'Male',
                'RELATIONSHIP': 'Parent',
                'SYMBIONT': 'N',
                'COLLECTOR_AFFILIATION': 'Lab',
                'DEPTH': '100',
                'ELEVATION': '200',
                'ORIGINAL_COLLECTION_DATE': '2021-12-31',
                'ORIGINAL_GEOGRAPHIC_LOCATION': 'OldCountry | OldRegion',
                'GAL': 'GAL001',
                'VOUCHER_ID': 'V123',
                'SPECIMEN_ID': 'S123',
                'GAL_SAMPLE_ID': 'GS123',
                'CULTURE_OR_STRAIN_ID': 'CS123'
            }
        )
        converter = IncomingSampleToEnaSampleConverter(
            mock_data_source.data_object_factory,
            converter_config
        )
        result = converter.convert(mock_one)
        mock_ena_datasource = MockEnaDataSource({})
        core_data_object(mock_ena_datasource)
        validator = EnaChecklistValidator(config=config, datasource=mock_ena_datasource)
        list(validator.validate(result))
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 3
