# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from typing import Iterable
from tol.sources.benchling import benchling
from tol.core import DataObject, DataSourceFilter, DataObjectToDataObjectOrUpdateConverter


class StsSampleToCasmBenchlingConverterFactory:
    RELATIONSHIPS = {
        'benchling_species': {
            'benchling_object_name': 'casm_species',
            'benchling_search_identifier': 'species_name',
            'sts_identifier': 'scientific_name',
            'sts_type': 'relationship',
            'relationship_identifier': 'target_species',
        },
        'benchling_donor': {
            'benchling_object_name': 'casm_donor',
            'benchling_search_identifier': 'id_donor_casm',
            'sts_identifier': 'ID_DONOR_CASM',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'benchling_tissue': {
            'benchling_object_name': 'casm_tissue',
            'benchling_search_identifier': 'id_tissue_casm',
            'sts_identifier': 'ID_TISSUE_CASM',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'benchling_sample_meta_data': {
            'benchling_object_name': 'casm_sample_metadata',
            'benchling_search_identifier': 'id_sample_casm_manual',
            'sts_identifier': 'sts_id',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'benchling_compliance_agreement': {
            'benchling_object_name': 'casm_compliance_agreement',
            'benchling_search_identifier': 'id_tissue_casm',
            'sts_identifier': 'HUMFRE_REFERENCE',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'benchling_sample_owner': {
            'benchling_object_name': 'casm_users',
            'benchling_search_identifier': 'Email',
            'sts_identifier': 'SANGER_RESPONSIBLE_SCIENTIST',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'benchling_gal': {
            'benchling_object_name': 'casm_gal',
            'benchling_search_identifier': 'Email',
            'sts_identifier': 'COLLABORATOR_ADDRESS',
            'sts_type': 'field',
            'relationship_identifier': None,
        },
        'sts_sex': {
            'identifier': 'name',
            'relationship_identifier': 'target_species_sex',
        },
        'sts_sampleset': {
            'identifier': 'sampleset_id',
            'relationship_identifier': 'sampleset',
        },
        'sts_sample_status': {
            'identifier': 'status',
            'relationship_identifier': 'sample_status',
        },
        'sts_hazard_group': {
            'identifier': 'level',
            'relationship_identifier': 'hazard_group',
        }
    }

    BENCHLING_OBJECT_MAP = {
        'casm_species': {
            'stored_values': {},
        },
        'casm_compliance_agreement': {
            'stored_values': {},
        },
        'casm_users': {
            'stored_values': {},
        },
        'casm_gal': {
            'stored_values': {},
        },
        'casm_donor': {
            'attribute_map': {
                'id_donor_casm': 'ID_DONOR_CASM',
                'species': 'benchling_species',
                'sex': 'sts_sex',
            },
            'primary_attribute': 'id_donor_casm',
            'benchling_relationships': ['benchling_species'],
            'sts_relationships': ['sts_sex'],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_tissue': {
            'attribute_map': {
                'donor_id': 'benchling_donor',
                'tissue_type': 'TISSUE_PHENOTYPE',
                'age': 'SPECIMEN_AGE_YEARS',
                'foetal_tissue': 'FETAL_TISSUE',
                'disease_status': 'WILDTYPE_DISEASE',
                'cancer_type': 'TISSUE_HISTOLOGY',
                'id_tissue_casm': 'ID_TISSUE_CASM',
                'country_of_origin': 'COUNTRY_OF_ORIGIN',
            },
            'primary_attribute': 'id_tissue_casm',
            'benchling_relationships': ['benchling_donor'],
            'sts_relationships': [],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_sample_metadata': {
            'attribute_map': {
                'tissue_id': 'benchling_tissue',
                'compliance_agreement': 'benchling_compliance_agreement',
                'sample_owner': 'benchling_sample_owner',
                # 'gal': 'sts_gal',
                'tissue_preparation': 'TISSUE_PREPARATION',
                'sts_id': 'id',
                'collaborator_name': 'COLLABORATOR_NAME',
                # 'sample_preparation': '',
                'responsible_pi': 'SANGER_RESPONSIBLE_PI',
                'responsible_scientist': 'SANGER_RESPONSIBLE_SCIENTIST',
                'sample_set_id': 'sts_sampleset',
            },
            'primary_attribute': 'sts_id',
            'benchling_relationships': [
                'benchling_tissue',
                'benchling_compliance_agreement',
                'benchling_sample_owner',
                # 'benchling_gal'
            ],
            'sts_relationships': ['sts_sampleset'],
            'converted_value_identifiers': [],
            'stored_values': {},
        },
        'casm_sample': {
            'attribute_map': {
                'sample_metadata_id': 'benchling_sample_meta_data',
                'sample_type': 'sample_format',
                'date_created': 'created_on',
                'safety_class': 'sts_hazard_group',
                'genetically_modified': 'genetically_modified',
                'status_manual': 'sts_sample_status',
                'programme_id_manual': 'INTERNAL_CASM_SAMPLE_NAME',
                'id_sample_casm_manual': 'ID_SAMPLE_CASM'
            },
            'primary_attribute': 'programme_id_manual',
            'benchling_relationships': [
                'benchling_sample_meta_data',
            ],
            'sts_relationships': [
                'sts_sample_status',
                'sts_hazard_group',
            ],
            'converted_value_identifiers': [],
            'stored_values': {},
        }
    }

    VALUE_REPLACEMENTS = {
        'sex': {
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

    def __init__(
            self,
            destination_object_type: str,
            previous_object_type: str = "",
            previous_objects: list = None
    ):
        self.destination_object_type = destination_object_type
        if previous_object_type and previous_objects:
            for previous_object in previous_objects:
                object_map = self.BENCHLING_OBJECT_MAP[previous_object_type]
                identifier = object_map['primary_attribute']
                key = getattr(previous_object, identifier)
                object_map['stored_values'][key] = previous_object

        self.benchling = benchling()
        benchling_type = self.benchling.benchling_types[self.destination_object_type]
        self.fields = self.benchling.schemas[benchling_type][self.destination_object_type]

    def get_converter_class(self) -> DataObjectToDataObjectOrUpdateConverter:
        factory = self

        class StsSampleToCasmBenchlingConverter(DataObjectToDataObjectOrUpdateConverter):
            def convert(self, data_object: DataObject) -> Iterable[DataObject]:
                sample = data_object
                object_map = factory.BENCHLING_OBJECT_MAP[factory.destination_object_type]
                primary_attr_id = object_map['primary_attribute']
                primary_attr = object_map['attribute_map'][primary_attr_id]
                if 'id' == primary_attr:
                    primary_attr_value = sample.id
                else:
                    primary_attr_value = sample.attributes.get(primary_attr)

                if not self._does_object_exist(primary_attr_value, primary_attr_id):
                    self._populate_relationships(sample)

                    attribute_map = object_map['attribute_map']
                    object_attributes = {
                        key: (
                            sample.id
                            if 'id' == attr_mapping
                            else sample.attributes.get(attr_mapping)
                        )
                        for key, attr_mapping in attribute_map.items()
                    }

                    self._sanitize_attributes(object_attributes)
                    object_map['converted_value_identifiers'] = \
                        object_map['converted_value_identifiers'] + [primary_attr]
                    print(object_attributes)
                    yield self._data_object_factory(
                        factory.destination_object_type,
                        sample.id,
                        attributes=object_attributes
                    )

            def _populate_relationships(self, sample):
                self._populate_benchling_relationships(sample)
                self._populate_sts_relationships(sample)

            def _populate_benchling_relationships(self, sample):
                """
                    This method populates the attributes with the values
                    from the benchling_relationships.
                    This population is handled through lookups to the benchling data source
                    or looking at the saved values in the config

                    Args:
                        sample: sample data object from sts

                    Returns:
                        None

                    Raises:
                        Exception if the relationship is not returned.
                        This is mainly because the relationships identified within
                        the benchling_relationships are almost always required.
                """
                object_type = factory.destination_object_type
                relationships = \
                    factory.BENCHLING_OBJECT_MAP[object_type]['benchling_relationships']

                for relationship_key in relationships:
                    relationship = factory.RELATIONSHIPS[relationship_key]
                    identifier = relationship['relationship_identifier']
                    search_value = None
                    if 'relationship' == relationship['sts_type'] and hasattr(sample, identifier):
                        try:
                            relationship_obj = next(iter(getattr(sample, identifier)))
                            search_value = getattr(
                                relationship_obj,
                                relationship['sts_identifier'],
                                None
                            )
                        except StopIteration:
                            continue
                    elif 'field' == relationship['sts_type']:
                        if 'sts_id' == relationship['sts_identifier']:
                            search_value = sample.id
                        else:
                            getattr(sample, relationship['sts_identifier'], None)

                    stored_values = factory.BENCHLING_OBJECT_MAP[object_type]['stored_values']
                    if search_value is not None:
                        search_value = self._sanitize_attribute(
                            relationship['benchling_search_identifier'],
                            search_value,
                            relationship['benchling_object_name'],
                        )

                        if search_value not in stored_values:
                            schema_filter = DataSourceFilter()
                            schema_filter.and_ = {
                                relationship['benchling_search_identifier']: {
                                    'eq': {
                                        'value': search_value
                                    }
                                },
                            }
                            filter_obj = DataSourceFilter()
                            filter_obj.and_ = {'schema_fields': schema_filter}

                            try:
                                benchling_item = next(
                                    iter(
                                        factory.benchling.get_list(
                                            relationship['benchling_object_name'],
                                            filter_obj
                                        )
                                    )
                                )
                                stored_values[search_value] = benchling_item.id
                            except StopIteration:
                                print('search_value')
                                print(search_value)
                                raise Exception(
                                    f'Sample not ready for import: Sample #{sample.id} '
                                    f'is missing the relationship for {relationship_key}'
                                )

                        sample.attributes[relationship_key] = stored_values[search_value]
                    else:
                        raise Exception(
                            f'Sample not ready for import: {sample.id} '
                            f'is missing the relationship for {relationship_key}'
                        )

            def _populate_sts_relationships(self, sample):
                """
                    This method populates the attributes with the values from the sts_relationships

                    Args:
                        sample: sample data object from sts

                    Returns:
                        None

                    Expects a StopIteration exception if the relationship does not have a value
                """
                object_type = factory.destination_object_type
                relationships = factory.BENCHLING_OBJECT_MAP[object_type]['sts_relationships']

                for relationship_key in relationships:
                    relationship = factory.RELATIONSHIPS[relationship_key]
                    identifier = relationship['relationship_identifier']

                    try:
                        relationship_obj = getattr(sample, identifier)

                        if isinstance(relationship_obj, Iterable):
                            relationship_obj = next(iter(relationship_obj))

                        value = getattr(relationship_obj, relationship['identifier'], None)
                        sample.attributes[relationship_key] = value

                    except StopIteration:
                        continue

            def _does_object_exist(self, attribute: any, identifier: str):
                """
                Checks if the object all ready exists within the
                Benchling ecosystem or is all ready loaded into memory

                Args:
                    attribute - the attribute value we are searching for
                    identifier - the identifier of the attribute within Benchling

                Expects:
                    StopIteration - if no object is returned from Benchling
                """
                object_map = factory.BENCHLING_OBJECT_MAP[factory.destination_object_type]
                stored_values = object_map['stored_values']
                converted_value_ids = object_map['converted_value_identifiers']
                attribute = self._sanitize_attribute(identifier, attribute)

                if attribute in stored_values or attribute in converted_value_ids:
                    return True

                schema_filter = DataSourceFilter()
                schema_filter.and_ = {identifier: {'eq': {'value': attribute}}}
                filter_obj = DataSourceFilter()
                filter_obj.and_ = {'schema_fields': schema_filter}

                try:
                    benchling_obj = next(
                        iter(
                            factory.benchling.get_list(
                                factory.destination_object_type,
                                filter_obj
                            )
                        )
                    )
                    self._return_objects.append(benchling_obj)
                    stored_values[attribute] = benchling_obj

                    return True
                except StopIteration:
                    return False

            def _sanitize_attributes(self, object_attributes):
                for key, value in object_attributes.items():
                    object_attributes[key] = self._sanitize_attribute(key, value)

            def _sanitize_attribute(self, key: str, value: any, object_type_override: str = ''):
                """
                    This method sanitises an attribute making sure its the
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
                if '' == object_type_override:
                    fields = factory.fields
                else:
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

        return StsSampleToCasmBenchlingConverter
