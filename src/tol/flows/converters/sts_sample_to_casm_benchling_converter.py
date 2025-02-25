# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT
import re
from typing import Iterable

from benchling_sdk.errors import BenchlingError
from benchling_sdk.models import NamingStrategy
from certifi import contents
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
            'identifier': 'sampleset_id',
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
    '''
        Map of sts relationship objects to call to. 
        These objects could are mainly used to query the relationships of the sample for a specific value
    '''

    BENCHLING_OBJECT_MAP = {
        'casm_species': {
            'attribute_map': {
                'species_name': 'target_species',
            },
            'primary_attribute': 'species_name',
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
        'casm_compliance_agreement': {
            'attribute_map': {
                'compliance_agreement_id': 'HUMFRE_REFERENCE',
            },
            'primary_attribute': 'compliance_agreement_id',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_users': {
            'attribute_map': {
                'Email': 'SANGER_RESPONSIBLE_SCIENTIST',
            },
            'primary_attribute': 'Email',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_donor': {
            'attribute_map': {
                'id_donor_casm': 'ID_DONOR_CASM',
                'species': 'casm_species',
                'sex': 'sex',
            },
            'primary_attribute': 'id_donor_casm',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': ['casm_species'],
            'sts_relationships': ['sex'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.NEW_IDS
        },
        'casm_tissue': {
            'attribute_map': {
                'donor_id': 'casm_donor',
                'tissue_type': 'TISSUE_PHENOTYPE',
                'age': 'SPECIMEN_AGE_YEARS',
                'foetal_tissue': 'FETAL_TISSUE',
                'disease_status': 'WILDTYPE_DISEASE',
                'cancer_type': 'TISSUE_HISTOLOGY',
                'id_tissue_casm': 'ID_TISSUE_CASM',
                'country_of_origin': 'COUNTRY_OF_ORIGIN',
            },
            'primary_attribute': 'id_tissue_casm',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': ['casm_donor'],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.NEW_IDS
        },
        'casm_sample_metadata': {
            'attribute_map': {
                'tissue_id': 'casm_tissue',
                'compliance_agreement': 'casm_compliance_agreement',
                'sample_owner': 'casm_users',
                'tissue_preparation': 'TISSUE_PREPARATION',
                'sts_id': 'id',
                'collaborator_name': 'COLLABORATOR_NAME',
                'responsible_pi': 'SANGER_RESPONSIBLE_PI',
                'responsible_scientist': 'SANGER_RESPONSIBLE_SCIENTIST',
                'sample_set_id': 'sampleset'
            },
            'primary_attribute': 'sts_id',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_tissue',
                'casm_compliance_agreement',
                'casm_users'
            ],
            'sts_relationships': ['sampleset'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
            'naming_strategy': NamingStrategy.NEW_IDS
        },
        'casm_sample': {
            'attribute_map': {
                'sample_metadata_id': 'casm_sample_metadata',
                'sample_type': 'sample_format',
                'date_created': 'created_on',
                'safety_class': 'hazard_group',
                'genetically_modified': 'genetically_modified',
                'status_manual': 'sample_status',
                'programme_id_manual': 'INTERNAL_CASM_SAMPLE_NAME',
                'id_sample_casm_manual': 'ID_SAMPLE_CASM'
            },
            'primary_attribute': 'id_sample_casm_manual',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample_metadata',
            ],
            'sts_relationships': [
                'sample_status',
                'hazard_group',
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {}
        },
        'casm_programme_id' : {
            'attribute_map': {
                'sample_id': 'casm_sample',
                'programme_id': 'INTERNAL_CASM_SAMPLE_NAME',
                'id_sample_casm': 'ID_SAMPLE_CASM'
            },
            'primary_attribute': 'sample_id',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample',
            ],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_sample_status' : {
            'attribute_map': {
                'sample_id': 'casm_sample',
                'status': 'sample_status'
            },
            'primary_attribute': 'sample_id',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_sample',
            ],
            'sts_relationships': [
                'sample_status'
            ],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        '10x10_box': {
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
        'casm_96_well_plate': {
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
        'casm_tube': {
            'attribute_map': {
                'barcode': 'tubeid',
                'parent_storage_id': 'box_and_position'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                '10x10_box',
            ],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'concatinated_values': ['box_and_position'],
            'stored_values': {},
        },
        'casm_well': {
            'attribute_map': {
                'barcode': 'plate_and_location_non_relationship',
                'parent_storage_id': 'plate_and_location'
            },
            'primary_attribute': 'barcode',
            'primary_attribute_type': 'schema_field',
            'benchling_relationships': [
                'casm_96_well_plate',
            ],
            'sts_relationships': ['storage_rack'],
            'polymorphic_benchling_relationships': [],
            'converted_value_identifiers': [],
            'concatinated_values': ['plate_and_location_non_relationship','plate_and_location'],
            'stored_values': {},
        },
        'transfer': {
            'attribute_map': {
                'source_entity_id': 'casm_sample',
                'destination_container_id': 'container',
                'transfer_quantity': 'VOLUME_UL',
                'transfer_concentration': 'CONCENTRATION_NG_UL',
            },
            'primary_attribute': None,
            'benchling_relationships': ['casm_sample'],
            'sts_relationships': [],
            'polymorphic_benchling_relationships': [
                'container'
            ],
            'converted_value_identifiers': [],
            'concatinated_values': [],
            'stored_values': {},
        }
    }
    '''
     Map of benchling objects to transform based on sts attributes. 
     If only stored_values are present then the object is mainly used for storing results in memory
    '''



    CONCATENATED_VALUES = {
        'plate_and_location': {
            'values':    [
                'casm_96_well_plate',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        },
        'plate_and_location_non_relationship': {
            'values':    [
                'storage_rack',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        },
        'box_and_position': {
            'values':    [
                '10x10_box',
                'TUBE_WELL_POSITION'
            ],
            'separator': ':'
        }
    }

    VALUE_REPLACEMENTS = {
        'sex': {
            'MALE': 'Male',
            'FEMALE': 'Female',
            'NOT_PROVIDED': 'Unknown'
        },
        'responsible_pi': {
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
        'genetically_modified': {
            'default': 'No'
        },
        'status_manual': {
            'ACCEPTED': 'Available'
        },
        'status': {
            'ACCEPTED': 'Available'
        },
        'species_name': {
            'Canis lupus familiaris': 'Canis familiaris'
        },
        'sample_type': {
            'inactivated biological sample from infectious organism': 'Tissue',
            'live biological sample from infectious organism': 'Tissue',
            'biological sample / tissue from non-infectious organism': 'Tissue',
            'default': 'DNA'
        }
    }
    '''
        Map of replacements for string objects. Mainly used for data cleanup
    '''

    DESTINATION_OBJECT_TYPES = {
        'box_or_plate': {
            'RACK_TUBE': "10x10_box",
            'PLATE_WELL': "casm_96_well_plate"
        },
        'container': {
            'RACK_TUBE': "casm_tube",
            'PLATE_WELL': "casm_well"
        }
    }
    '''
        Map of the dynamic object types
    '''

    POLYMORPHIC_RELATIONSHIP_OBJECT_TYPES = {
        'container': {
            'RACK_TUBE': "casm_tube",
            'PLATE_WELL': "casm_well"
        }
    }
    '''
        Map of the polymorphic relationship objects
    '''

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
            raise Exception('Please include a detect_destination_type to auto-detect')
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
                        sample = sample,
                        detect_destination_type = factory.detect_destination_type
                    )
                    factory.populate_destination(destination_object_type)
                object_map = factory.BENCHLING_OBJECT_MAP[factory.destination_object_type]
                if not self._does_object_exist(factory.destination_object_type, sample, object_map):
                    self._populate_relationships(sample, object_map)

                    object_attributes = self._populate_object_attributes(object_map, sample)

                    if 'transfer' != factory.destination_object_type:
                        object_map['converted_value_identifiers'] = \
                            object_map['converted_value_identifiers'] + [primary_attr_value]

                    if 'naming_strategy' in object_map and object_map['naming_strategy']:
                        object_attributes['naming_strategy'] = object_map['naming_strategy']

                    print(object_attributes)
                    exit(0)
                    yield self._data_object_factory(
                        factory.destination_object_type,
                        sample.id,
                        attributes=object_attributes
                    )

            def __get_primary_attribute(self, object_map, primary_attr_id, sample):
                primary_attr = object_map['attribute_map'][primary_attr_id]

                if primary_attr in object_map['sts_relationships']:
                    self._populate_relationships(sample, object_map)

                if 'concatinated_values' in object_map and primary_attr in object_map['concatinated_values']:
                    self._populate_relationships(sample, object_map)
                    self._populate_concatenated_attributes(sample, object_map['attribute_map'])

                if 'id' == primary_attr:
                    primary_attr_value = sample.id
                else:
                    primary_attr_value = sample.attributes.get(primary_attr)
                return primary_attr_value

            def _populate_object_attributes(self, object_map, sample):
                attribute_map = object_map['attribute_map']
                self._populate_concatenated_attributes(sample, attribute_map)

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

            @staticmethod
            def _populate_concatenated_attributes(sample, attribute_map):
                if not sample.attributes.get('concatenated_attributes_populated', False):
                    for key, attr_mapping in attribute_map.items():
                        if attr_mapping in factory.CONCATENATED_VALUES:
                            separator = factory.CONCATENATED_VALUES[attr_mapping]['separator']

                            # Strip out any trailing 0 for the TUBE_WELL_POSITION as benchling strips this out on save
                            # so it breaks any search queires for bar codes
                            values = [
                                re.sub(r'([A-Za-z]+)0', r'\1', sample.attributes.get(attribute, ''))\
                                    if attribute == 'TUBE_WELL_POSITION' else sample.attributes.get(attribute, '')
                                for attribute in factory.CONCATENATED_VALUES[attr_mapping]['values']
                            ]

                            sample.attributes[attr_mapping] = separator.join(filter(None, values))
                    sample.attributes['concatenated_attributes_populated'] = True

            def _populate_relationships(self, sample, object_map):
                if not sample.attributes.get('relationships_populated', False):
                    self._populate_benchling_relationships(sample, object_map)
                    self._populate_sts_relationships(sample, object_map)
                    sample.attributes['relationships_populated'] = True

            def _populate_benchling_relationships(self, sample, object_map):
                """
                Populates the STS sample object attributes with Benchling-compatible values.
                This ensures Benchling relationship IDs replace human-readable elements.

                Args:
                    sample: Sample data object from STS.
                    object_map: The nested JSON config from the factory.

                Raises:
                    Exception: If a required relationship is missing or cannot be populated.
                """
                self._populate_polymorphic_benchling_relationships(sample, object_map)

                for benchling_object_identifier in object_map['benchling_relationships']:
                    relationship_object_map = factory.BENCHLING_OBJECT_MAP[benchling_object_identifier]
                    benchling_primary_attribute = relationship_object_map['primary_attribute']
                    sts_attribute_identifier = relationship_object_map['attribute_map'][benchling_primary_attribute]

                    if (
                        'concatinated_values' in relationship_object_map
                        and sts_attribute_identifier in relationship_object_map['concatinated_values']
                    ):
                        self._populate_relationships(sample, relationship_object_map)
                        self._populate_concatenated_attributes(sample, relationship_object_map['attribute_map'])

                    search_value = self._get_relationship_search_value(
                        sample,
                        sts_attribute_identifier,
                        relationship_object_map
                    )

                    if search_value is not None:
                        search_value = self._sanitize_attribute(
                            benchling_primary_attribute, search_value, benchling_object_identifier
                        )

                        if search_value in relationship_object_map['stored_values']:
                            sample.attributes[benchling_object_identifier] = \
                            relationship_object_map['stored_values'][search_value]

                        benchling_object_id = self._get_benchling_object_id(
                            object_type=benchling_object_identifier,
                            search_identifier=benchling_primary_attribute,
                            search_value=search_value
                        )

                        if benchling_object_id is not None:
                            sample.attributes[benchling_object_identifier] = benchling_object_id
                            continue

                    raise Exception(
                        f'Sample not ready for import: {sample.id} '
                        f'is missing the relationship for {benchling_object_identifier}'
                    )

            @staticmethod
            def _get_relationship_search_value(sample, sts_attribute_identifier, relationship_object_map):
                """
                Determines the appropriate search value for a relationship.

                Args:
                    sample: The sample data object from STS.
                    sts_attribute_identifier: The attribute name in the STS object.
                    relationship_object_map: The mapping of relationships in Benchling.

                Returns:
                    The appropriate search value or None.
                """
                if (
                    sts_attribute_identifier in relationship_object_map['sts_relationships']
                    and sts_attribute_identifier in factory.STS_OBJECT_MAP
                ):
                    relationship_identifier = factory.STS_OBJECT_MAP[sts_attribute_identifier]['relationship_identifier']
                    sts_relationship_attr = getattr(sample, relationship_identifier, None)

                    if isinstance(sts_relationship_attr, Iterable) and not isinstance(sts_relationship_attr, str):
                        relationship_obj = next(iter(sts_relationship_attr), None)
                    else:
                        relationship_obj = sts_relationship_attr

                    if relationship_obj is not None:
                        return getattr(
                            relationship_obj,
                            factory.STS_OBJECT_MAP[sts_attribute_identifier]['identifier'],
                            None
                        )

                return sample.id if sts_attribute_identifier == 'sts_id' \
                    else getattr(sample, sts_attribute_identifier, None)

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
                        relationship_object_type and
                        relationship_object_type not in object_map['benchling_relationships']
                    ):

                        key_for_relationship_object_type = next(
                            (key for key, value in object_map['attribute_map'].items() if relationship == value),
                            None
                        )

                        if key_for_relationship_object_type:
                            object_map['benchling_relationships'].append(relationship_object_type)
                            object_map['attribute_map'][key_for_relationship_object_type] = relationship_object_type


            @staticmethod
            def _populate_sts_relationships(sample, object_map):
                """
                    This method populates the attributes with the values from the sts_relationships

                    Args:
                        sample: sample data object from sts

                    Returns:
                        None

                    Expects a StopIteration exception if the relationship does not have a value
                """
                for sts_object_identifier in object_map['sts_relationships']:
                    relationship_object_map = factory.STS_OBJECT_MAP[sts_object_identifier]
                    relationship_identifier = relationship_object_map['relationship_identifier']

                    try:
                        relationship_object = getattr(sample, relationship_identifier)

                        if isinstance(relationship_object, Iterable):
                            relationship_object = next(iter(relationship_object))

                        value = getattr(relationship_object, relationship_object_map['identifier'], None)
                        sample.attributes[sts_object_identifier] = value

                    except StopIteration:
                        continue

            def _does_object_exist(self, destination_object_type, sample,object_map):
                """
                Checks if the object all ready exists within the
                Benchling ecosystem or is all ready loaded into memory

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
                    identifier = object_map['primary_attribute']
                    attribute = self.__get_primary_attribute(object_map, primary_attr_id, sample)
                    attribute = self._sanitize_attribute(identifier, attribute)

                    if attribute in stored_values or attribute in converted_value_ids:
                        return True

                    benchling_object_id = self._get_benchling_object_id(
                        object_type=destination_object_type,
                        search_identifier=identifier,
                        search_value=attribute,
                        add_to_return=True
                    )

                    if benchling_object_id is not None:
                        factory.BENCHLING_OBJECT_MAP[factory.destination_object_type]['stored_values'][attribute] = benchling_object_id

                        return True

                return False

            def _check_sample_transfers_done(self, sample, object_map):
                self._populate_relationships(sample, object_map)

                container_id = sample.attributes.get(object_map['attribute_map']['destination_container_id'])
                if not container_id:
                    return False

                contents_found = True
                try:
                    contents = factory.benchling.get_conainer_contents(container_id)

                    if not contents:
                        contents_found = False
                except BenchlingError as e:
                    contents_found = False

                return contents_found

            def _get_benchling_object_id(
                self,
                object_type:str ,
                search_identifier:str,
                search_value:str,
                add_to_return: bool = False
            ) -> str|None:
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
                elif factory.benchling.benchling_types[object_type] in ['box','plate','container','location']:
                    if 'barcode' == search_identifier:
                        search_identifier = 'barcodes'
                    filter_object.and_ = {search_identifier: {'in_list': {'value': [search_value]}}}
                elif factory.benchling.benchling_types[object_type] in ['assay_result']:
                    filter_object.and_ = {'entity_id': {'eq': {'value': [search_value]}}}
                else:
                    raise Exception('Unsupported search')

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
            def _get_destination_object_type(
                    sample,
                    detect_destination_type: str,
                    raise_exception: bool = True
            ) -> str | None:
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
                        f'Sample is not ready for import: Sample #{sample.id} has unsupported destination type')

                return None

        return StsSampleToCasmBenchlingConverter
