# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT
import re
from typing import Iterable

from benchling_sdk.errors import BenchlingError
from benchling_sdk.models import NamingStrategy

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter, DataSourceFilter
from tol.sources.benchling import benchling


class StsSampleToCasmBenchlingConverterFactory:
    STS_OBJECT_MAP = {
        'storage_rack': {
            'identifier': 'id',
            'relationship_identifier': 'storage_rack',
        },
        'sex': {
            'identifier': 'name',
            'relationship_identifier': 'target_species_sex',
        },
        'sampleset': {
            'identifier': 'name',
            'relationship_identifier': 'sampleset',
        },
        'sample_status': {
            'identifier': 'status',
            'relationship_identifier': 'sample_status',
        },
        'hazard_group': {
            'identifier': 'level',
            'relationship_identifier': 'hazard_group',
        },
        'target_species': {
            'identifier': 'scientific_name',
            'relationship_identifier': 'target_species',
        },
        'labwhere': {
            'identifier': 'labwhere_id',
            'relationship_identifier': 'storage_rack',
        },
    }
    """
        Map of sts relationship objects to call to.
        These objects could are mainly used to query the
        relationships of the sample for a specific value
    """
    BENCHLING_OBJECT_MAP = {
        'casm_species_v1': {
            'attribute_map': {
                'species_name_v1': 'target_species',
            },
            'primary_attribute': 'species_name_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [],
            'sts_relationships': ['target_species'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'storage': {
            'attribute_map': {
                'barcode': 'labwhere',
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'attribute',
            'benchling_relationships': [],
            'sts_relationships': ['labwhere'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_compliance_agreement_v1': {
            'attribute_map': {
                'compliance_agreement_id_v1': 'HUMFRE_REFERENCE',
            },
            'primary_attribute': 'compliance_agreement_id_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_user_v1': {
            'attribute_map': {
                'email_username_v1': 'SANGER_RESPONSIBLE_SCIENTIST',
            },
            'primary_attribute': 'email_username_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_donor_v1': {
            'attribute_map': {
                'id_donor_casm_v1': 'ID_DONOR_CASM',
                'species_v1': 'casm_species_v1',
                'sex_v1': 'sex',
            },
            'primary_attribute': 'id_donor_casm_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': ['casm_species_v1'],
            'sts_relationships': ['sex'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS
        },
        'casm_tissue_v1': {
            'attribute_map': {
                'donor_id_v1': 'casm_donor_v1',
                'tissue_type_v1': 'TISSUE_PHENOTYPE',
                'age_v1': 'SPECIMEN_AGE_YEARS',
                'foetal_tissue_v1': 'FETAL_TISSUE',
                'disease_status_v1': 'WILDTYPE_DISEASE',
                'cancer_type_v1': 'TISSUE_HISTOLOGY',
                'id_tissue_casm_v1': 'ID_TISSUE_CASM',
                'country_of_origin_v1': 'COUNTRY_OF_ORIGIN',
            },
            'primary_attribute': 'id_tissue_casm_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': ['casm_donor_v1'],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS
        },
        'casm_sample_metadata_v1': {
            'attribute_map': {
                'tissue_id_v1': 'casm_tissue_v1',
                'compliance_agreement_v1': 'casm_compliance_agreement_v1',
                'responsible_scientist_v1': 'casm_user_v1',
                'tissue_preparation_v1': 'TISSUE_PREPARATION',
                'sts_id_v1': 'id',
                'collaborator_name_v1': 'COLLABORATOR_NAME',
                'responsible_pi_v1': 'SANGER_RESPONSIBLE_PI',
                'sample_set_id_v1': 'sampleset'
            },
            'primary_attribute': 'sts_id_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_tissue_v1',
                'casm_compliance_agreement_v1',
                'casm_user_v1'
            ],
            'sts_relationships': ['sampleset'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS
        },
        'casm_sample_v1': {
            'attribute_map': {
                'sample_metadata_id_v1': 'casm_sample_metadata_v1',
                'sample_type_v1': 'sample_format',
                'date_created_v1': 'created_on',
                'hazard_group_v1': 'hazard_group',
                'genetically_modified_v1': 'genetically_modified',
                'status_manual_v1': 'sample_status',
                'programme_id_manual_v1': 'INTERNAL_CASM_SAMPLE_NAME',
                'id_sample_casm_manual_v1': 'ID_SAMPLE_CASM'
            },
            'primary_attribute': 'id_sample_casm_manual_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample_metadata_v1',
            ],
            'sts_relationships': [
                'sample_status',
                'hazard_group',
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS
        },
        'casm_programme_id_v1': {
            'attribute_map': {
                'sample_id_v1': 'casm_sample_v1',
                'programme_id_v1': 'INTERNAL_CASM_SAMPLE_NAME',
                'id_sample_casm_v1': 'ID_SAMPLE_CASM'
            },
            'primary_attribute': 'sample_id_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample_v1',
            ],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_sample_status_v1': {
            'attribute_map': {
                'sample_id_v1': 'casm_sample_v1',
                'status_v1': 'sample_status'
            },
            'primary_attribute': 'sample_id_v1',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample_v1',
            ],
            'sts_relationships': [
                'sample_status'
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        '12x12_box': {
            'attribute_map': {
                'barcode': 'storage_rack',
                'parent_storage_id': 'storage'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'attribute',
            'benchling_relationships': [
                'storage',
            ],
            'sts_relationships': [
                'storage_rack'
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_96_well_plate_v1': {
            'attribute_map': {
                'barcode': 'storage_rack',
                'parent_storage_id': 'storage'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'attribute',
            'benchling_relationships': [
                'storage',
            ],
            'sts_relationships': [
                'storage_rack'
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_tube_v1': {
            'attribute_map': {
                'barcode': 'tubeid',
                'parent_storage_id': 'box_and_position'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                '12x12_box',
            ],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'concatenated_values': ['box_and_position'],
            'stored_values': {},
        },
        'casm_well_v1': {
            'attribute_map': {
                'barcode': 'plate_and_location_non_relationship',
                'parent_storage_id': 'plate_and_location'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_96_well_plate_v1',
            ],
            'sts_relationships': ['storage_rack'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'concatenated_values': ['plate_and_location_non_relationship', 'plate_and_location'],
            'stored_values': {},
        },
        'transfer': {
            'attribute_map': {
                'source_entity_id': 'casm_sample_v1',
                'destination_container_id': 'container',
                'transfer_quantity': 'VOLUME_UL',
                'transfer_concentration': 'CONCENTRATION_NG_UL',
            },
            'primary_attribute': None,
            'benchling_relationships': ['casm_sample_v1'],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [
                'container'
            ],
            'converted_value_identifiers': [],
            'concatenated_values': [],
            'stored_values': {},
        }
    }

    """
     Map of benchling objects to transform based on sts attributes.
     If only stored_values are present then the object is mainly used for storing results in memory
    """

    CONCATENATED_VALUES = {
        'plate_and_location': {
            'values': [
                'casm_96_well_plate_v1',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        },
        'plate_and_location_non_relationship': {
            'values': [
                'storage_rack',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        },
        'box_and_position': {
            'values': [
                '12x12_box',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        }
    }
    """
    Map of the values that need to be concatenated for the use within benchling
    """

    VALUE_REPLACEMENTS = {
        'sex_v1': {
            'MALE': 'Male',
            'FEMALE': 'Female',
            'NOT_PROVIDED': 'Unknown'
        },
        'responsible_pi_v1': {
            'default': 'other',
            'da1': 'David Adams',
            'im3': 'Inigo Martincorena',
            'jn5': 'Jyoti Nangalia',
            'ly2': 'Lucy Yates',
            'mg12': 'Mathew Garnett',
            'mrs': 'Mike Stratton',
            'pc8': 'Peter Campbell',
            'pj3': 'Phil Jones',
            'rr11': 'Raheleh Rahbari',
            'sb31': 'Sam Behjati',
            'tjm': 'Thomas Mitchell',
        },
        'genetically_modified_v1': {
            'default': 'No'
        },
        'status_manual_v1': {
            'ACCEPTED': 'Available'
        },
        'status_v1': {
            'ACCEPTED': 'Available'
        },
        'species_name_v1': {
            'Canis lupus familiaris': 'Canis familiaris'
        },
        'sample_type_v1': {
            'inactivated biological sample from infectious organism': 'Tissue',
            'live biological sample from infectious organism': 'Tissue',
            'biological sample / tissue from non-infectious organism': 'Tissue',
            'default': 'DNA'
        }
    }
    """
        Map of replacements for string objects. Mainly used for data cleanup
    """

    DESTINATION_OBJECT_TYPES = {
        'box_or_plate': {
            'RACK_TUBE': '12x12_box',
            'PLATE_WELL': 'casm_96_well_plate_v1'
        },
        'container': {
            'RACK_TUBE': 'casm_tube_v1',
            'PLATE_WELL': 'casm_well_v1'
        }
    }
    """
        Map of the dynamic object types
    """

    POLYMORPHIC_RELATIONSHIP_OBJECT_TYPES = {
        'container': {
            'RACK_TUBE': 'casm_tube_v1',
            'PLATE_WELL': 'casm_well_v1'
        }
    }
    """
        Map of the polymorphic relationship objects
    """

    destination_object_type: str
    fields: Iterable[any]

    def __init__(
            self,
            destination_object_type: str = '',
            previous_object_type: str = '',
            previous_objects: list = None,
            detect_destination: bool = False,
            detect_destination_type: str = '',
    ):
        self.detect_destination = detect_destination
        self.benchling = benchling()
        if not detect_destination:
            self.populate_destination(destination_object_type)
        elif detect_destination_type == '':
            raise Exception(
                'Configuration error of flow: Please include a '
                'detect_destination_type to auto-detect'
            )
        else:
            self.detect_destination_type = detect_destination_type

        if previous_object_type and previous_objects:
            for previous_object in previous_objects:
                object_map = self.BENCHLING_OBJECT_MAP[previous_object_type]
                identifier = object_map['primary_attribute']
                key = getattr(previous_object, identifier)
                object_map['stored_values'][key] = previous_object

    def populate_destination(self, destination_object_type):
        self.destination_object_type = destination_object_type

        if 'transfer' != self.destination_object_type:
            benchling_type = self.benchling.benchling_types[self.destination_object_type]
            self.fields = self.benchling.schemas[benchling_type][self.destination_object_type]

    def get_converter_class(self) -> DataObjectToDataObjectOrUpdateConverter:
        factory = self

        class StsSampleToCasmBenchlingConverter(DataObjectToDataObjectOrUpdateConverter):
            def convert(self, data_object: DataObject) -> Iterable[DataObject]:
                sample = data_object

                if factory.detect_destination:
                    destination_object_type = self._get_destination_object_type(
                        sample=sample,
                        detect_destination_type=factory.detect_destination_type
                    )
                    factory.populate_destination(destination_object_type)

                object_map = factory.BENCHLING_OBJECT_MAP[factory.destination_object_type]
                if not self._does_object_exist(
                    factory.destination_object_type,
                    sample,
                    object_map
                ):
                    self._populate_relationships(sample, object_map)

                    object_attributes = self._populate_object_attributes(object_map, sample)

                    if 'transfer' != factory.destination_object_type:
                        primary_attribute = self._get_object_primary_attribute_value(
                            object_map,
                            sample
                        )
                        object_map['converted_value_identifiers'] = \
                            object_map['converted_value_identifiers'] + [primary_attribute]

                    if 'naming_strategy' in object_map and object_map['naming_strategy']:
                        object_attributes['naming_strategy'] = object_map['naming_strategy']

                    yield self._data_object_factory(
                        factory.destination_object_type,
                        sample.id,
                        attributes=object_attributes
                    )

            @staticmethod
            def _get_destination_object_type(
                    sample,
                    detect_destination_type: str,
                    raise_exception: bool = True
            ) -> str | None:
                """
                Determines the destination object type for a sample.

                Args:
                    sample - the sample used to determine the destination object type
                    detect_destination_type - the type of destination to detect
                    raise_exception - whether to raise an exception if the
                    destination type is unsupported

                Expects:
                    Exception - if the sample has an unsupported destination type
                    and raise_exception is True

                Returns:
                    str | None - the detected destination object type or None if not found
                    and raise_exception is False
                """
                if (
                        hasattr(sample, 'manifest')
                        and hasattr(sample.manifest, 'manifest_type')
                        and sample.manifest.manifest_type in factory.
                        DESTINATION_OBJECT_TYPES[detect_destination_type]
                ):
                    return factory.DESTINATION_OBJECT_TYPES[detect_destination_type][
                        sample.manifest.manifest_type]

                if raise_exception:
                    raise Exception(
                        f'Sample is not ready for import: Sample #{sample.id}'
                        f' has unsupported destination type for dynamic conversion'
                    )

                return None

            @staticmethod
            def _sanitize_attribute(key: str, value: any, object_type_override: str = ''):
                """
                    This static method sanitizes an attribute making sure it's the
                    correct type expected by Benchling, it will also transform the value of
                    the attribute to a predetermined safe value for
                    Benchling this is configured in VALUE_REPLACEMENTS.

                    Args:
                         key -  This argument specifies the key of the attribute,
                         value -  This argument specifies the value of the attribute to be cleaned
                         object_type_override – This argument specifies the cleanup actions to
                         be performed if the attribute does not belong to
                         the destination object of the converter.

                    Return:
                        Any - depends on the value provided and the cleanup performed
                """
                fields = getattr(factory, 'fields', [])

                if '' != object_type_override:
                    benchling_type = factory.benchling.benchling_types[object_type_override]
                    if (
                            benchling_type
                            and object_type_override in factory.benchling.schemas[benchling_type]
                    ):
                        fields = factory.benchling.schemas[benchling_type][object_type_override]

                if fields and key in fields:
                    if 'int' == fields[key]['type']:
                        if value:
                            value = int(value)
                        else:
                            value = 0

                    if 'str' == fields[key]['type']:
                        if value:
                            value = str(value)

                        if key in factory.VALUE_REPLACEMENTS:
                            if value in factory.VALUE_REPLACEMENTS[key]:
                                value = factory.VALUE_REPLACEMENTS[key][value]
                            elif 'default' in factory.VALUE_REPLACEMENTS[key]:
                                value = factory.VALUE_REPLACEMENTS[key]['default']

                        if fields[key]['is_multi']:
                            value = [value]

                    if 'genetically_modified' == key:
                        value = factory.VALUE_REPLACEMENTS[key]['default']

                return value

            @staticmethod
            def _get_sts_relationship_attribute_value(relationship_object_identifier: str, sample):
                """
                Retrieves the attribute value for an STS relationship.

                Args:
                    relationship_object_identifier - the identifier of the relationship object
                    sample - the sample from which to retrieve the relationship attribute value

                Returns:
                    str | None - the attribute value of the relationship object, or None
                """
                attribute_value = None
                relationship_object_map = factory.STS_OBJECT_MAP[relationship_object_identifier]
                sts_relationship = getattr(
                    sample,
                    relationship_object_map['relationship_identifier'],
                    None
                )

                if (
                    isinstance(sts_relationship, Iterable)
                    and not isinstance(sts_relationship, str)
                ):
                    relationship_object = next(iter(sts_relationship), None)
                else:
                    relationship_object = sts_relationship

                if relationship_object is not None:
                    attribute_value = getattr(
                        relationship_object,
                        relationship_object_map['identifier'],
                        None
                    )

                return attribute_value

            def _populate_concatenated_attributes(self, sample, object_map):
                """
                Populates concatenated attributes for a given sample.

                Args:
                    sample - the sample whose concatenated attributes need to be populated
                    object_map - a mapping of attributes relevant to the sample

                Returns:
                    None
                """

                self._populate_relationships(sample, object_map)

                for key, attribute_mapping in object_map['attribute_map'].items():
                    if (
                        attribute_mapping in factory.CONCATENATED_VALUES
                        and sample.attributes.get(attribute_mapping, None) is None
                    ):
                        separator = factory.CONCATENATED_VALUES[attribute_mapping]['separator']

                        # Strip out any trailing 0 for the TUBE_WELL_POSITION as benchling strips
                        # this out on save so it breaks any search queries for bar codes
                        values = [
                            re.sub(
                                r'([A-Za-z]+)0',
                                r'\1',
                                sample.attributes.get(attribute, '') or ''
                            ) if attribute == 'TUBE_WELL_POSITION' else sample.attributes.get(
                                attribute, ''
                            ) for attribute in factory.CONCATENATED_VALUES[
                                attribute_mapping]['values']
                        ]

                        sample.attributes[attribute_mapping] = separator.join(filter(None, values))

            def _populate_sts_relationships(self, sample, object_map):
                """
                    This method populates the attributes with the values from the sts_relationships

                    Args:
                        sample: sample data object from sts

                    Returns:
                        None

                    Expects a StopIteration exception if the relationship does not have a value
                """
                for relationship_object_identifier in object_map['sts_relationships']:
                    if sample.attributes.get(relationship_object_identifier, None) is None:
                        sample.attributes[relationship_object_identifier] = \
                            self._get_sts_relationship_attribute_value(
                                relationship_object_identifier, sample)

            def _does_object_exist(self, destination_object_type, sample, object_map):
                """
                Checks if the object all ready exists within the
                Benchling ecosystem or is already loaded into memory

                Args:
                    destination_object_type - type of object we are looking for
                    sample - the sample we are using to get the search values

                Expects:
                    StopIteration - if no object is returned from Benchling
                """

                stored_values = object_map['stored_values']
                converted_value_ids = object_map['converted_value_identifiers']

                if 'transfer' == destination_object_type:
                    return self._check_sample_transfers_done(sample, object_map)
                else:
                    attribute = self._get_object_primary_attribute_value(object_map, sample)

                    if attribute in stored_values or attribute in converted_value_ids:
                        return True

                    benchling_object_id = self._get_benchling_object_id(
                        object_type=destination_object_type,
                        search_identifier=object_map['primary_attribute'],
                        search_value=attribute,
                        add_to_return=True
                    )

                    if benchling_object_id is not None:
                        factory.BENCHLING_OBJECT_MAP[factory.destination_object_type][
                            'stored_values'][attribute] = benchling_object_id

                        return True

                return False

            def _check_sample_transfers_done(self, sample, object_map) -> bool:
                """
                Checks if a sample has any transfers by retrieving the container for the sample.

                Args:
                    sample - the sample to check for completed transfers
                    object_map - a mapping of attributes relevant to the sample

                Expects:
                    BenchlingError - if an error occurs while retrieving container contents

                Returns:
                    bool - True if the container has contents, False otherwise

                Raises:
                    Exception: If teh sample has no container in Bechnling
                """
                self._populate_relationships(sample, object_map)

                container_id = sample.attributes.get(
                    object_map['attribute_map']['destination_container_id']
                )
                if not container_id:
                    raise Exception(
                        f'Sample: {sample.id} not ready for transfer as '
                        f'it does not have a container registered in benchling'
                    )

                contents_found = True
                try:
                    contents = factory.benchling.get_container_contents(container_id)

                    if not contents:
                        contents_found = False
                except BenchlingError:
                    contents_found = False

                return contents_found

            def _get_object_primary_attribute_value(self, object_map, sample):
                """
                Retrieves the primary attribute value for a given object map from the sts sample.

                Args:
                    object_map - a mapping of attributes relevant to the object
                    sample - the sample from which to retrieve the primary attribute value

                Returns:
                    str | None - the primary attribute value, or None if not found
                """
                benchling_attribute_identifier = object_map['primary_attribute']
                sts_attribute_identifier = object_map['attribute_map'][
                    benchling_attribute_identifier]

                if (
                        sts_attribute_identifier in object_map['sts_relationships']
                        and sts_attribute_identifier in factory.STS_OBJECT_MAP
                ):
                    self._populate_sts_relationships(sample, object_map)
                elif (
                    'concatenated_values' in object_map
                    and sts_attribute_identifier in object_map['concatenated_values']
                ):
                    self._populate_concatenated_attributes(sample, object_map)

                if sts_attribute_identifier in ['id', 'sts_id']:
                    attribute_value = sample.id
                else:
                    attribute_value = sample.attributes.get(sts_attribute_identifier, None)

                attribute_value = self._sanitize_attribute(
                    sts_attribute_identifier,
                    attribute_value
                )

                return attribute_value

            def _populate_relationships(self, sample, object_map):
                """
                Populates the relationships for a given sample based on the object_map

                Args:
                    sample - the sample whose relationships need to be populated
                    object_map - a mapping of attributes relevant to the sample

                Returns:
                    None
                """
                self._populate_benchling_relationships(sample, object_map)
                self._populate_sts_relationships(sample, object_map)

            def _populate_benchling_relationships(self, sample, object_map):
                """
                Populates the STS sample object attributes with Benchling-compatible values.
                This ensures Benchling relationship IDs replace human-readable elements.

                Args:
                    sample: Sample data object from STS.
                    object_map: The nested JSON config from the factory.

                Raises:
                    Exception: If a required relationship is missing or cannot be populated.

                Returns:
                    None
                """
                self._populate_polymorphic_benchling_relationships(sample, object_map)

                for benchling_object_identifier in object_map['benchling_relationships']:
                    relationship_object_map = factory.BENCHLING_OBJECT_MAP[
                        benchling_object_identifier]
                    if sample.attributes.get(benchling_object_identifier, None) is None:
                        search_value = self._get_object_primary_attribute_value(
                            relationship_object_map,
                            sample
                        )

                        if search_value is not None:
                            if search_value in relationship_object_map['stored_values']:
                                benchling_object_id = relationship_object_map['stored_values'][
                                    search_value]
                            else:
                                benchling_object_id = self._get_benchling_object_id(
                                    object_type=benchling_object_identifier,
                                    search_identifier=relationship_object_map['primary_attribute'],
                                    search_value=search_value
                                )

                            if benchling_object_id is not None:
                                sample.attributes[benchling_object_identifier] = \
                                    benchling_object_id
                                continue

                        raise Exception(
                            f'Sample not ready for import: {sample.id} is missing the '
                            f'benchling relationship for {benchling_object_identifier}'
                        )

            def _populate_object_attributes(self, object_map, sample):
                """
                Populates the attributes for an object using the given sample.

                Args:
                    object_map - a mapping of attributes relevant to the object
                    sample - the sample from which to populate the object attributes

                Returns:
                    dict - a dictionary of populated object attributes
                """
                attribute_map = object_map['attribute_map']
                self._populate_concatenated_attributes(sample, object_map)

                object_attributes = {
                    key: (
                        sample.id
                        if 'id' == attr_mapping
                        else sample.attributes.get(attr_mapping)
                    )
                    for key, attr_mapping in attribute_map.items()
                }
                self._sanitize_attributes(object_attributes)
                return object_attributes

            def _populate_polymorphic_benchling_relationships(self, sample, object_map):
                """
                Populates the 'benchling_relationships' list in object_map with detected
                polymorphic relationships for the given sample.

                Args:
                    sample: The sample object being processed.
                    object_map (dict): A mapping containing 'polymorphic_benchling_relationships'
                                       and 'benchling_relationships' lists.

                The function iterates over 'polymorphic_benchling_relationships', determines
                the destination object type, and appends it to 'benchling_relationships'
                if it's not already present.
                """
                for relationship in object_map.get('polymorphic_benchling_relationships', []):
                    relationship_object_type = self._get_destination_object_type(
                        sample=sample,
                        detect_destination_type=relationship,
                        raise_exception=False
                    )

                    if (
                        relationship_object_type
                        and relationship_object_type not in object_map['benchling_relationships']
                    ):

                        key_for_relationship_object_type = next(
                            (
                                key for key, value in object_map['attribute_map'].items()
                                if relationship == value
                            ),
                            None
                        )

                        if key_for_relationship_object_type:
                            object_map['benchling_relationships'].append(relationship_object_type)
                            object_map['attribute_map'][key_for_relationship_object_type] = \
                                relationship_object_type

            def _get_benchling_object_id(
                self,
                object_type: str,
                search_identifier: str,
                search_value: str,
                add_to_return: bool = False
            ) -> str | None:
                """
                This method is used to get the benchling object id for its given args

                Args:
                    object_type: String identifying the benchling object type
                    search_identifier: The identifier of the attribute of the benchling object
                    search_value: The values we are searching for
                """
                filter_object = DataSourceFilter()
                if 'custom_entity' == factory.benchling.benchling_types[object_type]:
                    schema_filter = DataSourceFilter()
                    schema_filter.and_ = {search_identifier: {'eq': {'value': search_value}}}
                    filter_object.and_ = {'schema_fields': schema_filter}
                elif (factory.benchling.benchling_types[object_type]
                      in ['box', 'plate', 'container', 'location']):
                    if 'barcode' == search_identifier:
                        search_identifier = 'barcodes'
                    filter_object.and_ = {
                        search_identifier: {'in_list': {'value': [search_value]}}
                    }
                elif factory.benchling.benchling_types[object_type] in ['assay_result']:
                    filter_object.and_ = {'entity_id': {'eq': {'value': [search_value]}}}
                else:
                    raise Exception(
                        f'Configuration error: Unsupported search of type {object_type}'
                    )

                try:
                    benchling_object = next(
                        iter(
                            factory.benchling.get_list(
                                object_type,
                                filter_object
                            )
                        )
                    )

                    if add_to_return:
                        self._return_objects.append(benchling_object)

                    return benchling_object.id
                except StopIteration:
                    return None

            def _sanitize_attributes(self, object_attributes):
                for key, value in object_attributes.items():
                    object_attributes[key] = self._sanitize_attribute(key, value)

        return StsSampleToCasmBenchlingConverter
