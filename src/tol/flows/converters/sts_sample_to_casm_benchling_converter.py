# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT
import logging
import re
from typing import Iterable, Any
from dataclasses import dataclass

from benchling_sdk.errors import BenchlingError
from benchling_sdk.models import NamingStrategy

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter, DataSourceFilter
from tol.sources.benchling import benchling


class StsSampleToCasmBenchlingConverterFactory:
    BOX_PLATE_SCHEMA_FIELD = 'BOX_PLATE_SCHEMA'
    BOX_PLATE_SCHEMA_DESTINATION = 'box_plate_schema'
    RACK_TUBE_MANIFEST_TYPE = 'RACK_TUBE'
    BOX_PLATE_SCHEMA_OBJECT_TYPES = {
        'production': {
            'Fluid X Rack 96': 'fluid_x_rack_96',
            '12x12 box': '12x12_box',
        },
        'staging': {
            'Fluid X Rack 96': 'fluid_x_rack_96',
            '12x12 box': '12x12_box_v2',
        },
    }

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
        'tray': {
            'identifier': 'tray_id',
            'relationship_identifier': 'storage_rack',
        },
        'gal': {
            'identifier': 'name',
            'relationship_identifier': 'gal',
        }
    }
    """
        Map of sts relationship objects to call to.
        These objects could are mainly used to query the
        relationships of the sample for a specific value
    """
    BENCHLING_OBJECT_MAP = {
        'production': {
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
                    'barcode': 'tray',
                },
                'primary_attribute': 'barcode',
                'primary_attribute_type': 'attribute',
                'benchling_relationships': [],
                'sts_relationships': ['tray'],
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
                'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS,                
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
                'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS,
                
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
                    'sample_set_id_v1': 'sampleset',
                    'gal_v1': 'gal'
                },
                'primary_attribute': 'sts_id_v1',
                'primary_attribute_type': 'schema_field',
                'benchling_relationships': [
                    'casm_tissue_v1',
                    'casm_user_v1'
                ],
                'benchling_multiselect_relationships': [
                    'casm_compliance_agreement_v1'
                ],
                'sts_relationships': ['sampleset', 'gal'],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'stored_values': {},
                'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS,
            },
            'casm_sample_v1': {
                'attribute_map': {
                    'sample_metadata_id_v1': 'casm_sample_metadata_v1',
                    'sample_type_v1': 'sample_format',
                    'date_created_v1': 'created_on',
                    'hazard_group_v1': 'computed_hazard_group',
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
                ],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'stored_values': {},
                'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS,
                
            },
            'casm_qc_result_v1': {
                'attribute_map': {
                    'total_volume_ul_v1': 'VOLUME_UL',
                    'concentration_ngul_v1': 'CONCENTRATION_NG_UL',
                    'sample_preparation_v1': 'TISSUE_PREPARATION',
                    'gel_result_v1': 'RNA_RIN',
                    'sample_id_v1': 'casm_sample_v1'
                },
                'primary_attribute': 'sample_id_v1',
                'primary_attribute_type': 'schema_field',
                'benchling_relationships': [
                    'casm_sample_v1',
                ],
                'sts_relationships': [],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'concatenated_values': [],
                'stored_values': {},
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
            'fluid_x_rack_96': {
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
                    # 'transfer_quantity': 'VOLUME_UL',
                    # 'transfer_concentration': 'CONCENTRATION_NG_UL',
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
        },
        'staging': {
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
                    'barcode': 'tray',
                },
                'primary_attribute': 'barcode',
                'primary_attribute_type': 'attribute',
                'benchling_relationships': [],
                'sts_relationships': ['tray'],
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
                'naming_strategy': NamingStrategy.NEW_IDS,
                
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
                'naming_strategy': NamingStrategy.NEW_IDS,
                
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
                    'sample_set_id': 'sampleset',
                    'gal': 'gal'
                },
                'primary_attribute': 'sts_id',
                'primary_attribute_type': 'schema_field',
                'benchling_relationships': [
                    'casm_tissue',
                    'casm_users'
                ],
                'benchling_multiselect_relationships': [
                    'casm_compliance_agreement'
                ],
                'sts_relationships': ['sampleset', 'gal'],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'stored_values': {},
                'naming_strategy': NamingStrategy.NEW_IDS,
                
            },
            'casm_sample': {
                'attribute_map': {
                    'sample_metadata_id': 'casm_sample_metadata',
                    'sample_type': 'sample_format',
                    'date_created': 'created_on',
                    'safety_class': 'computed_hazard_group',
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
                ],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'stored_values': {},
                'naming_strategy': NamingStrategy.REPLACE_NAMES_FROM_PARTS,
                
            },
            'casm_qc_result': {
                'attribute_map': {
                    'total_volume_ul': 'VOLUME_UL',
                    'concentration_ngul': 'CONCENTRATION_NG_UL',
                    'sample_preparation': 'TISSUE_PREPARATION',
                    'rin_value': 'RNA_RIN',
                    'sample_id_v2': 'casm_sample'
                },
                'primary_attribute': 'sample_id_v2',
                'primary_attribute_type': 'schema_field',
                'benchling_relationships': [
                    'casm_sample',
                ],
                'sts_relationships': [],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'concatenated_values': [],
                'stored_values': {},
            },
            'casm_programme_id': {
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
            'casm_sample_status': {
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
            '12x12_box_v2': {
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
            'fluid_x_rack_96': {
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
                    '12x12_box_v2',
                ],
                'sts_relationships': [],
                'polymorphic_benchling_relationships': [],
                'converted_value_identifiers': [],
                'concatenated_values': ['box_and_position'],
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
                'concatenated_values': ['plate_and_location_non_relationship', 'plate_and_location'],
                'stored_values': {},
            },
            'transfer': {
                'attribute_map': {
                    'source_entity_id': 'casm_sample',
                    'destination_container_id': 'container',
                    # 'transfer_quantity': 'VOLUME_UL',
                    # 'transfer_concentration': 'CONCENTRATION_NG_UL',
                },
                'primary_attribute': None,
                'benchling_relationships': ['casm_sample'],
                'sts_relationships': [],
                'polymorphic_benchling_relationships': [
                    'container'
                ],
                'converted_value_identifiers': [],
                'concatenated_values': [],
                'stored_values': {},
            }
        }
    }

    """
     Map of benchling objects to transform based on sts attributes.
     If only stored_values are present then the object is mainly used for storing results in memory
    """

    CONCATENATED_VALUES = {
        'production': {
            'plate_and_location': {
                'values': [
                    'casm_96_well_plate_v1',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            },
            'plate_and_location_non_relationship': {
                'values': [
                    'storage_rack',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            },
            'box_and_position': {
                'values': [
                    '12x12_box',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            }
        },
        'staging': {
            'plate_and_location': {
                'values': [
                    'casm_96_well_plate',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            },
            'plate_and_location_non_relationship': {
                'values': [
                    'storage_rack',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            },
            'box_and_position': {
                'values': [
                    '12x12_box_v2',
                    {
                        'primary': 'pos_in_rack',
                        'fallback': 'TUBE_WELL_POSITION'
                    }
                ],
                'separator': ':'
            }
        }
    }
    """
    Map of the values that need to be concatenated for the use within benchling
    """

    VALUE_REPLACEMENTS = {
        'production': {
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
                'biological sample/tissue from non-infectious organism': 'Tissue',
                'default': 'DNA'
            }
        },
        'staging': {
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
                'biological sample/tissue from non-infectious organism': 'Tissue',
                'default': 'DNA'
            },

        }
    }
    """
        Map of replacements for string objects. Mainly used for data cleanup
    """

    COMPUTED_VALUES = {
        'production': {
            'computed_hazard_group': {
                'computed_from': 'sample_format',
                'values': {
                    'Tissue': 'HG2',
                    'default': 'HG1',
                }
            }
        },
        'staging': {
            'computed_hazard_group': {
                'computed_from': 'sample_format',
                'values': {
                    'Tissue': 'HG2',
                    'default': 'HG1',
                }
            }
        }
    }

    DESTINATION_OBJECT_TYPES = {
        'production': {
            'box_or_plate': {
                'RACK_TUBE': BOX_PLATE_SCHEMA_DESTINATION,
                'PLATE_WELL': 'casm_96_well_plate_v1'
            },
            'container': {
                'RACK_TUBE': 'casm_tube_v1',
                'PLATE_WELL': 'casm_well_v1'
            }
        },
        'staging': {
            'box_or_plate': {
                'RACK_TUBE': BOX_PLATE_SCHEMA_DESTINATION,
                'PLATE_WELL': 'casm_96_well_plate'
            },
            'container': {
                'RACK_TUBE': 'casm_tube',
                'PLATE_WELL': 'casm_well'
            }
        }
    }
    """
        Map of the dynamic object types
    """

    MULTISELECT_BENCHLING_RELATIONSHIPS = {
        'production': {
            'casm_compliance_agreement_v1': {
                'legal': {
                    'attribute_map': {
                        'compliance_agreement_id_v1': 'LEGAL_AGREEMENT',
                    },
                    'primary_attribute': 'compliance_agreement_id_v1',
                    'primary_attribute_type': 'schema_field',
                    'secondary_attribute': 'compliance_agreement_type_v1',
                    'secondary_attribute_value': 'Legal',
                    'benchling_relationships': [],
                    'sts_relationships': [],
                    'polymorphic_benchling_relationships': [],
                    'converted_value_identifiers': [],
                    'stored_values': {},
                },
                'humfre': {
                    'attribute_map': {
                        'compliance_agreement_id_v1': 'HUMFRE_REFERENCE',
                    },
                    'primary_attribute': 'compliance_agreement_id_v1',
                    'primary_attribute_type': 'schema_field',
                    'secondary_attribute': 'compliance_agreement_type_v1',
                    'secondary_attribute_value': 'HuMFre',
                    'benchling_relationships': [],
                    'sts_relationships': [],
                    'polymorphic_benchling_relationships': [],
                    'converted_value_identifiers': [],
                    'stored_values': {},
                }
            }
        },
        'staging': {
            'casm_compliance_agreement': {
                'legal': {
                    'attribute_map': {
                        'compliance_agreement_id': 'LEGAL_AGREEMENT',
                    },
                    'primary_attribute': 'compliance_agreement_id',
                    'primary_attribute_type': 'schema_field',
                    'secondary_attribute': 'compliance_agreement_type',
                    'secondary_attribute_value': 'Legal',
                    'benchling_relationships': [],
                    'sts_relationships': [],
                    'polymorphic_benchling_relationships': [],
                    'converted_value_identifiers': [],
                    'stored_values': {},
                },
                'humfre': {
                    'attribute_map': {
                        'compliance_agreement_id': 'HUMFRE_REFERENCE',
                    },
                    'primary_attribute': 'compliance_agreement_id',
                    'primary_attribute_type': 'schema_field',
                    'secondary_attribute': 'compliance_agreement_type',
                    'secondary_attribute_value': 'HuMFre',
                    'benchling_relationships': [],
                    'sts_relationships': [],
                    'polymorphic_benchling_relationships': [],
                    'converted_value_identifiers': [],
                    'stored_values': {},
                }
            }
        }
    }

    destination_object_type: str
    fields: Iterable[Any]

    def __init__(
            self,
            destination_object_type: str = '',
            previous_object_type: str = '',
            previous_value_map: dict[str, str] | None = None,
            detect_destination: bool = False,
            detect_destination_type: str = '',
            mode: str = 'staging',
    ):
        """Initialize a converter factory for CASM Benchling objects.

        Args:
            destination_object_type: Concrete Benchling object type to convert to.
            previous_object_type: Previously loaded object type whose ids should be cached.
            previous_value_map: Primary-value to Benchling-id map from a previous load.
            detect_destination: Whether to detect destination type per sample.
            detect_destination_type: Dynamic destination alias to detect.
            mode: CASM converter mode, either staging or production.

        Raises:
            ValueError: If mode is not production or staging.
            Exception: If dynamic destination detection is enabled without an alias.
        """
        if mode not in ['production', 'staging']:
            raise ValueError('Mode must be either "production" or "staging"')

        self.detect_destination = detect_destination
        self.benchling = benchling()
        self.mode = mode
        if not detect_destination:
            self.populate_destination(destination_object_type)
        elif detect_destination_type == '':
            raise Exception(
                'Configuration error of flow: Please include a '
                'detect_destination_type to auto-detect'
            )
        else:
            self.detect_destination_type = detect_destination_type

        if previous_object_type and previous_value_map:
            object_map = self.BENCHLING_OBJECT_MAP[self.mode][previous_object_type]
            object_map['stored_values'].update(previous_value_map)

    @staticmethod
    def _is_missing_value(value: Any) -> bool:
        """Return whether a value should be treated as missing.

        Args:
            value: Value to inspect.

        Returns:
            bool: True for None, empty strings, and empty lists.
        """
        return value is None or value == '' or value == []

    @staticmethod
    def _sample_attribute(sample: DataObject, attribute_name: str) -> Any:
        """Read an attribute from a sample attributes dict or object property.

        Args:
            sample: STS sample data object to inspect.
            attribute_name: Attribute or property name to resolve.

        Returns:
            Any: Resolved attribute value, or None when unavailable.
        """
        attributes = getattr(sample, 'attributes', {}) or {}
        if isinstance(attributes, dict) and attribute_name in attributes:
            return attributes.get(attribute_name)
        return getattr(sample, attribute_name, None)

    @classmethod
    def _box_plate_schema_value_from_mapping(cls, mapping: dict[str, Any]) -> Any:
        """Resolve BOX_PLATE_SCHEMA from a flat or nested metadata mapping.

        Args:
            mapping: Sample attribute or metadata mapping to inspect.

        Returns:
            Any: Box-plate schema value, or None when not present.
        """
        if cls.BOX_PLATE_SCHEMA_FIELD in mapping:
            return mapping.get(cls.BOX_PLATE_SCHEMA_FIELD)

        for metadata_key in ('ext', 'custom', 'metadata', 'custom_metadata'):
            nested_value = mapping.get(metadata_key)
            if (
                    isinstance(nested_value, dict)
                    and cls.BOX_PLATE_SCHEMA_FIELD in nested_value
            ):
                return nested_value.get(cls.BOX_PLATE_SCHEMA_FIELD)

        return None

    @classmethod
    def get_box_plate_schema_value(cls, sample: DataObject) -> Any:
        """Resolve the configured box-plate schema value from a sample.

        Args:
            sample: STS sample data object to inspect.

        Returns:
            Any: Trimmed box-plate schema value, or None when missing.
        """
        attributes = getattr(sample, 'attributes', {}) or {}
        if isinstance(attributes, dict):
            value = cls._box_plate_schema_value_from_mapping(attributes)
            if not cls._is_missing_value(value):
                return value.strip() if isinstance(value, str) else value

        for metadata_key in ('ext', 'custom', 'metadata', 'custom_metadata'):
            metadata = cls._sample_attribute(sample, metadata_key)
            if isinstance(metadata, dict):
                value = cls._box_plate_schema_value_from_mapping(metadata)
                if not cls._is_missing_value(value):
                    return value.strip() if isinstance(value, str) else value

        return None

    @classmethod
    def get_manifest_type(cls, sample: DataObject) -> str | None:
        """Resolve the manifest type associated with a sample.

        Args:
            sample: STS sample data object to inspect.

        Returns:
            str | None: Manifest type, or None when no manifest is attached.
        """
        manifest = getattr(sample, 'manifest', None)
        return getattr(manifest, 'manifest_type', None)

    @classmethod
    def get_storage_rack_id(cls, sample: DataObject) -> Any:
        """Resolve the storage rack id associated with a sample.

        Args:
            sample: STS sample data object to inspect.

        Returns:
            Any: Storage rack id, or None when no rack can be resolved.
        """
        storage_rack = cls._sample_attribute(sample, 'storage_rack')
        if not cls._is_missing_value(storage_rack):
            if isinstance(storage_rack, DataObject) or hasattr(storage_rack, 'id'):
                return getattr(storage_rack, 'id', None)
            if (
                    isinstance(storage_rack, Iterable)
                    and not isinstance(storage_rack, str)
            ):
                storage_rack = next(iter(storage_rack), None)
                if (
                        isinstance(storage_rack, DataObject)
                        or hasattr(storage_rack, 'id')
                ):
                    return getattr(storage_rack, 'id', None)
                if not cls._is_missing_value(storage_rack):
                    return storage_rack
            else:
                return storage_rack

        relationship_object_map = cls.STS_OBJECT_MAP['storage_rack']
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
            return getattr(
                relationship_object,
                relationship_object_map['identifier'],
                None
            )

        return None

    @classmethod
    def allowed_box_plate_schema_values(cls, mode: str) -> list[str]:
        """Return allowed BOX_PLATE_SCHEMA values for a converter mode.

        Args:
            mode: CASM converter mode, either staging or production.

        Returns:
            list[str]: Allowed human-readable box-plate schema values.
        """
        return list(cls.BOX_PLATE_SCHEMA_OBJECT_TYPES[mode])

    @classmethod
    def get_box_plate_schema_object_type(cls, mode: str, sample: DataObject) -> str:
        """Resolve the Benchling box or rack object type for a rack-tube sample.

        Args:
            mode: CASM converter mode, either staging or production.
            sample: STS sample data object to inspect.

        Returns:
            str: Benchling object type for the sample's box-plate schema.

        Raises:
            ValueError: If the sample is missing BOX_PLATE_SCHEMA or has an
                unsupported schema value.
        """
        box_plate_schema = cls.get_box_plate_schema_value(sample)
        rack_id = cls.get_storage_rack_id(sample) or '<unknown>'

        if cls._is_missing_value(box_plate_schema):
            raise ValueError(
                f'Rack {rack_id} is missing {cls.BOX_PLATE_SCHEMA_FIELD}'
            )

        schema_object_types = cls.BOX_PLATE_SCHEMA_OBJECT_TYPES[mode]
        if box_plate_schema not in schema_object_types:
            allowed_values = ', '.join(cls.allowed_box_plate_schema_values(mode))
            raise ValueError(
                f'Rack {rack_id} has unsupported {cls.BOX_PLATE_SCHEMA_FIELD} '
                f'value {box_plate_schema!r}; allowed values are: {allowed_values}'
            )

        return schema_object_types[box_plate_schema]

    @classmethod
    def destination_object_type_for_sample(
            cls,
            mode: str,
            sample: DataObject,
            detect_destination_type: str,
            raise_exception: bool = True
    ) -> str | None:
        """Resolve the concrete destination object type for a sample.

        Args:
            mode: CASM converter mode, either staging or production.
            sample: STS sample data object to inspect.
            detect_destination_type: Dynamic destination alias to resolve.
            raise_exception: Whether to raise when the destination is unsupported.

        Returns:
            str | None: Concrete Benchling object type, or None when unsupported
                and raise_exception is false.

        Raises:
            Exception: If the sample manifest cannot be mapped and raise_exception is true.
            ValueError: If rack-tube box-plate schema selection fails.
        """
        destination_object_types = cls.DESTINATION_OBJECT_TYPES[mode].get(
            detect_destination_type,
            {},
        )
        manifest_type = cls.get_manifest_type(sample)

        if (
                detect_destination_type == 'box_or_plate'
                and manifest_type == cls.RACK_TUBE_MANIFEST_TYPE
        ):
            if raise_exception:
                return cls.get_box_plate_schema_object_type(mode, sample)

            try:
                return cls.get_box_plate_schema_object_type(mode, sample)
            except ValueError:
                return None

        if manifest_type in destination_object_types:
            return destination_object_types[manifest_type]

        if raise_exception:
            raise Exception(
                f'Sample is not ready for import: Sample #{sample.id}'
                f' has unsupported destination type for dynamic conversion'
            )

        return None

    @classmethod
    def apply_box_plate_schema_relationships(
            cls,
            mode: str,
            destination_object_type: str,
            sample: DataObject,
            object_map: dict[str, Any],
    ) -> None:
        """Adjust rack-tube container relationships for the sample's schema.

        Args:
            mode: CASM converter mode, either staging or production.
            destination_object_type: Destination Benchling object type being converted.
            sample: STS sample data object to inspect.
            object_map: Object map to mutate with the selected box relationship.

        Raises:
            ValueError: If rack-tube box-plate schema selection fails.
        """
        tube_object_type = cls.DESTINATION_OBJECT_TYPES[mode]['container'][
            cls.RACK_TUBE_MANIFEST_TYPE
        ]
        if destination_object_type != tube_object_type:
            return

        selected_box_object_type = cls.get_box_plate_schema_object_type(mode, sample)
        box_object_types = set(cls.BOX_PLATE_SCHEMA_OBJECT_TYPES[mode].values())
        relationships = list(object_map.get('benchling_relationships', []))
        updated_relationships = []
        replaced_box_relationship = False

        for relationship in relationships:
            if relationship in box_object_types:
                replaced_box_relationship = True
                if selected_box_object_type not in updated_relationships:
                    updated_relationships.append(selected_box_object_type)
            else:
                updated_relationships.append(relationship)

        if not replaced_box_relationship:
            updated_relationships.append(selected_box_object_type)

        object_map['benchling_relationships'] = updated_relationships

    @classmethod
    def concatenated_value_for_sample(
            cls,
            mode: str,
            sample: DataObject,
            attribute_mapping: str,
    ) -> dict[str, Any]:
        """Return concatenation config adjusted for the sample when needed.

        Args:
            mode: CASM converter mode, either staging or production.
            sample: STS sample data object to inspect for dynamic box type.
            attribute_mapping: Configured concatenated attribute key.

        Returns:
            dict[str, Any]: Concatenation configuration for the sample.

        Raises:
            ValueError: If dynamic box type resolution fails for box_and_position.
        """
        concatenated_value = cls.CONCATENATED_VALUES[mode][attribute_mapping]
        if attribute_mapping != 'box_and_position':
            return concatenated_value

        values = list(concatenated_value['values'])
        values[0] = cls.get_box_plate_schema_object_type(mode, sample)
        return {
            **concatenated_value,
            'values': values,
        }

    def object_map_for_sample(
            self,
            destination_object_type: str,
            sample: DataObject,
    ) -> dict[str, Any]:
        """Return an object map adjusted for a sample's dynamic relationships.

        Args:
            destination_object_type: Destination Benchling object type.
            sample: STS sample data object to inspect.

        Returns:
            dict[str, Any]: Object map to use for conversion.

        Raises:
            ValueError: If dynamic box-plate schema selection fails.
        """
        object_map = self.BENCHLING_OBJECT_MAP[self.mode][destination_object_type]
        self.apply_box_plate_schema_relationships(
            self.mode,
            destination_object_type,
            sample,
            object_map,
        )
        return object_map

    def populate_destination(self, destination_object_type):
        """Set the converter destination and cache schema fields for it.

        Args:
            destination_object_type: Benchling object type to convert to.
        """
        self.destination_object_type = destination_object_type

        if 'transfer' != self.destination_object_type:
            benchling_type = self.benchling.benchling_types[self.destination_object_type]
            self.fields = self.benchling.schemas[benchling_type][self.destination_object_type]

    def get_converter_class(self) -> DataObjectToDataObjectOrUpdateConverter:
        """Build the concrete DataObject converter class for this factory.

        Returns:
            DataObjectToDataObjectOrUpdateConverter: Converter class configured by
                this factory instance.
        """
        factory = self

        class StsSampleToCasmBenchlingConverter(DataObjectToDataObjectOrUpdateConverter):
            @dataclass(slots=True, frozen=True, kw_only=True)
            class Config:
                pass

            __slots__ = ['__config']
            __config: Config

            def __init__(self, data_object_factory, config: Config) -> None:
                """Initialize the CASM Benchling data object converter.

                Args:
                    data_object_factory: Factory used to create destination data objects.
                    config: Converter configuration object.
                """
                super().__init__(data_object_factory)
                self.__config = config
                self._data_object_factory = data_object_factory

            def convert(self, data_object: DataObject) -> Iterable[DataObject]:
                """Convert an STS sample into a Benchling data object when needed.

                Args:
                    data_object: STS sample data object to convert.

                Yields:
                    DataObject: Benchling data object ready for loading.
                """
                sample = data_object

                if factory.detect_destination:
                    destination_object_type = self._get_destination_object_type(
                        sample=sample,
                        detect_destination_type=factory.detect_destination_type
                    )
                    factory.populate_destination(destination_object_type)

                object_map = factory.object_map_for_sample(
                    factory.destination_object_type,
                    sample,
                )
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

                    print('object_attributes')
                    print(object_attributes)

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
                """Determine the destination object type for a sample.

                Args:
                    sample: STS sample used to determine the destination object type.
                    detect_destination_type: Dynamic destination alias to resolve.
                    raise_exception: Whether to raise if the destination is unsupported.

                Returns:
                    str | None: Detected destination object type, or None when
                        unsupported and raise_exception is false.

                Raises:
                    Exception: If the sample has an unsupported destination type and
                        raise_exception is true.
                    ValueError: If rack-tube box-plate schema selection fails.
                """
                return factory.destination_object_type_for_sample(
                    factory.mode,
                    sample,
                    detect_destination_type,
                    raise_exception,
                )

            @staticmethod
            def _sanitize_attribute(key: str, value: Any, object_type_override: str = ''):
                """Coerce and replace a value according to Benchling schema metadata.

                Args:
                    key: Benchling field or attribute key to sanitize.
                    value: Raw value from STS or relationship resolution.
                    object_type_override: Optional object type whose schema should be
                        used instead of the current destination schema.

                Returns:
                    Any: Value coerced into the shape expected by Benchling.
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

                    if 'str' == fields[key]['type'] and not isinstance(value, (list, tuple, set)):
                        if value:
                            value = str(value)

                        if key in factory.VALUE_REPLACEMENTS[factory.mode]:
                            if value in factory.VALUE_REPLACEMENTS[factory.mode][key]:
                                value = factory.VALUE_REPLACEMENTS[factory.mode][key][value]
                            elif 'default' in factory.VALUE_REPLACEMENTS[factory.mode][key]:
                                value = factory.VALUE_REPLACEMENTS[factory.mode][key]['default']

                        if fields[key]['is_multi']:
                            value = [value]

                    if fields[key]['is_multi'] and isinstance(value, (list, tuple, set)):
                        for v in value:
                            if 'str' == fields[key]['type']:
                                v = str(v)
                            elif 'int' == fields[key]['type']:
                                v = int(v)
                            
                    if 'genetically_modified' == key:
                        value = factory.VALUE_REPLACEMENTS[factory.mode][key]['default']

                return value

            @staticmethod
            def _get_sts_relationship_attribute_value(relationship_object_identifier: str, sample):
                """Retrieve the configured identifying value for an STS relationship.

                Args:
                    relationship_object_identifier: STS relationship key in STS_OBJECT_MAP.
                    sample: STS sample containing the relationship.

                Returns:
                    Any: Relationship identifying value, or None when unavailable.
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
                """Populate configured concatenated attributes on a sample.

                Args:
                    sample: STS sample data object to inspect and mutate.
                    object_map: Object map containing concatenated value configuration.

                Raises:
                    Exception: If required source values are missing.
                    ValueError: If dynamic box-plate schema selection fails.
                """
                self._populate_relationships(sample, object_map)

                for key, attribute_mapping in object_map['attribute_map'].items():
                    if (
                            attribute_mapping in factory.CONCATENATED_VALUES[factory.mode]
                            and sample.attributes.get(attribute_mapping, None) is None
                    ):
                        concatenated_value = factory.concatenated_value_for_sample(
                            factory.mode,
                            sample,
                            attribute_mapping,
                        )
                        separator = concatenated_value['separator']

                        values = {}
                        for attribute in concatenated_value['values']:
                            attribute_key, value = self._resolve_concatenated_attribute_value(
                                sample,
                                attribute
                            )
                            values[attribute_key] = value

                        missing_attributes = [
                            attribute
                            for attribute, value in values.items()
                            if value is None or value == ''
                        ]
                        if missing_attributes:
                            raise Exception(
                                f'Sample not ready for import: {sample.id} is missing '
                                f'the value(s) {missing_attributes} needed to build '
                                f'{attribute_mapping}'
                            )

                        sample.attributes[attribute_mapping] = separator.join(
                            str(value) for value in values.values()
                        )

            @staticmethod
            def _resolve_concatenated_attribute_value(sample, attribute):
                """Resolve one value used in a concatenated attribute.

                Args:
                    sample: STS sample data object to inspect.
                    attribute: Source attribute name or primary/fallback mapping.

                Returns:
                    tuple[str, Any]: Display key and sanitized source value.
                """
                if isinstance(attribute, dict):
                    primary_attribute = attribute['primary']
                    fallback_attribute = attribute.get('fallback')

                    value = sample.attributes.get(primary_attribute)
                    selected_attribute = primary_attribute
                    if value is None or value == '':
                        value = sample.attributes.get(fallback_attribute)
                        selected_attribute = fallback_attribute

                    attribute_key = f'{primary_attribute} or {fallback_attribute}'
                    return attribute_key, StsSampleToCasmBenchlingConverter._sanitize_position_value(
                        selected_attribute,
                        value
                    )

                value = sample.attributes.get(attribute)
                return attribute, StsSampleToCasmBenchlingConverter._sanitize_position_value(
                    attribute,
                    value
                )

            @staticmethod
            def _sanitize_position_value(attribute, value):
                """Normalize rack or well position values before conversion.

                Args:
                    attribute: Attribute name associated with the value.
                    value: Raw source position value.

                Returns:
                    Any: Normalized position value, or the original value for other fields.
                """
                # Strip out any trailing 0 as Benchling strips this out on save,
                # which breaks search queries for barcodes.
                if attribute in ['pos_in_rack', 'TUBE_WELL_POSITION']:
                    return re.sub(r'([A-Za-z]+)0', r'\1', value or '')

                return value

            def _populate_sts_relationships(self, sample, object_map):
                """Populate sample attributes from configured STS relationships.

                Args:
                    sample: STS sample data object to mutate.
                    object_map: Object map listing STS relationships to resolve.
                """
                for relationship_object_identifier in object_map['sts_relationships']:
                    if sample.attributes.get(relationship_object_identifier, None) is None:
                        sample.attributes[relationship_object_identifier] = \
                            self._get_sts_relationship_attribute_value(
                                relationship_object_identifier, sample)

            def _ensure_primary_attribute_available(self, sample, object_map):
                """Populate a primary relationship id when the primary field is relational.

                Args:
                    sample: STS sample data object to mutate.
                    object_map: Object map containing primary attribute metadata.
                """
                primary_attribute = object_map['primary_attribute']
                mapped_attribute = object_map['attribute_map'][primary_attribute]

                if mapped_attribute not in object_map.get('benchling_relationships', []):
                    return

                if sample.attributes.get(mapped_attribute) is not None:
                    return

                relationship_object_map = factory.BENCHLING_OBJECT_MAP[factory.mode][mapped_attribute]
                search_value = self._get_object_primary_attribute_value(
                    relationship_object_map,
                    sample
                )

                if search_value is None:
                    return

                if search_value in relationship_object_map['stored_values']:
                    sample.attributes[mapped_attribute] = relationship_object_map[
                        'stored_values'
                    ][search_value]
                    return

                benchling_object_id = self._get_benchling_object_id(
                    object_type=mapped_attribute,
                    search_identifier=relationship_object_map['primary_attribute'],
                    search_value=search_value
                )

                if benchling_object_id is not None:
                    sample.attributes[mapped_attribute] = benchling_object_id

            def _does_object_exist(self, destination_object_type, sample, object_map):
                """Check whether a destination object already exists or is cached.

                Args:
                    destination_object_type: Benchling object type to search.
                    sample: STS sample data object used to derive search values.
                    object_map: Object map containing primary attribute metadata.

                Returns:
                    bool: True when the object already exists or is cached in memory.

                Raises:
                    Exception: If transfer lookup cannot resolve a required container.
                    BenchlingError: If a Benchling lookup fails unexpectedly.
                """

                stored_values = object_map['stored_values']
                converted_value_ids = object_map['converted_value_identifiers']

                if 'transfer' == destination_object_type:
                    return self._check_sample_transfers_done(sample, object_map)
                else:
                    self._ensure_primary_attribute_available(sample, object_map)
                    attribute = self._get_object_primary_attribute_value(object_map, sample)

                    if attribute is None:
                        return False

                    if attribute in stored_values or attribute in converted_value_ids:
                        return True

                    benchling_object_id = self._get_benchling_object_id(
                        object_type=destination_object_type,
                        search_identifier=object_map['primary_attribute'],
                        search_value=attribute,
                        add_to_return=True
                    )

                    if benchling_object_id is not None:
                        factory.BENCHLING_OBJECT_MAP[factory.mode][factory.destination_object_type][
                            'stored_values'][attribute] = benchling_object_id

                        return True

                return False

            def _check_sample_transfers_done(self, sample, object_map) -> bool:
                """Check whether the destination container already has contents.

                Args:
                    sample: STS sample data object to inspect.
                    object_map: Object map containing transfer relationship metadata.

                Returns:
                    bool: True when the destination container has contents.

                Raises:
                    Exception: If the sample has no container in Benchling.
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
                """Resolve and sanitize the primary attribute value for an object map.

                Args:
                    object_map: Object map containing primary attribute metadata.
                    sample: STS sample data object to inspect.

                Returns:
                    Any: Primary attribute value, or None when unavailable.

                Raises:
                    Exception: If a required concatenated source value is missing.
                    ValueError: If dynamic box-plate schema selection fails.
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
                """Populate all configured relationship values on a sample.

                Args:
                    sample: STS sample data object to mutate.
                    object_map: Object map containing relationship metadata.

                Raises:
                    Exception: If a required Benchling relationship cannot be resolved.
                """
                self._populate_benchling_relationships(sample, object_map)
                self._populate_multiselect_benchling_relationships(sample, object_map)
                self._populate_sts_relationships(sample, object_map)

            def _populate_benchling_relationships(self, sample, object_map):
                """Populate Benchling relationship ids on a sample.

                Args:
                    sample: Sample data object from STS.
                    object_map: Object map containing Benchling relationship metadata.

                Raises:
                    Exception: If a required relationship is missing or cannot be populated.
                """
                self._populate_polymorphic_benchling_relationships(sample, object_map)

                for benchling_object_identifier in object_map['benchling_relationships']:
                    relationship_object_map = factory.BENCHLING_OBJECT_MAP[factory.mode][
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
                """Build Benchling object attributes from a sample.

                Args:
                    object_map: Object map describing attribute mappings.
                    sample: STS sample data object to convert.

                Returns:
                    dict: Benchling-ready object attributes.

                Raises:
                    Exception: If required concatenated or relationship values are missing.
                    ValueError: If dynamic box-plate schema selection fails.
                """
                attribute_map = object_map['attribute_map']
                self._populate_concatenated_attributes(sample, object_map)

                object_attributes = {}
                resolved_values = {}

                for key, attr_mapping in attribute_map.items():
                    if self._is_computed_attribute(attr_mapping):
                        continue

                    object_attributes[key] = self._resolve_attribute_value(
                        attr_mapping,
                        sample
                    )
                    resolved_values[attr_mapping] = object_attributes[key]
                    self._sanitize_resolved_attribute(
                        key,
                        attr_mapping,
                        object_attributes,
                        resolved_values
                    )

                if 'transfer' == factory.destination_object_type:
                    object_attributes['transfer_quantity'] = 0.001
                    object_attributes['transfer_concentration'] = 0.001
                    resolved_values['transfer_quantity'] = object_attributes[
                        'transfer_quantity'
                    ]
                    resolved_values['transfer_concentration'] = object_attributes[
                        'transfer_concentration'
                    ]
                    self._sanitize_resolved_attribute(
                        'transfer_quantity',
                        'transfer_quantity',
                        object_attributes,
                        resolved_values
                    )
                    self._sanitize_resolved_attribute(
                        'transfer_concentration',
                        'transfer_concentration',
                        object_attributes,
                        resolved_values
                    )

                self._populate_computed_attributes(
                    object_attributes,
                    attribute_map,
                    resolved_values
                )
                return object_attributes

            def _resolve_attribute_value(self, attr_mapping, sample):
                """Resolve a mapped STS attribute value from a sample.

                Args:
                    attr_mapping: STS attribute mapping identifier.
                    sample: STS sample data object to inspect.

                Returns:
                    Any: Sample id for id mappings, otherwise a sample attribute value.
                """
                if 'id' == attr_mapping:
                    return sample.id

                return sample.attributes.get(attr_mapping)

            @staticmethod
            def _is_computed_attribute(attr_mapping):
                """Check whether an attribute mapping is computed by the factory.

                Args:
                    attr_mapping: STS attribute mapping identifier.

                Returns:
                    bool: True when the mapping is configured as computed.
                """
                return attr_mapping in factory.COMPUTED_VALUES[factory.mode]

            def _sanitize_resolved_attribute(
                    self,
                    key,
                    attr_mapping,
                    object_attributes,
                    resolved_values
            ):
                """Sanitize an object attribute and update the resolved-value cache.

                Args:
                    key: Benchling field or attribute key.
                    attr_mapping: STS attribute mapping identifier for the value.
                    object_attributes: Mutable Benchling attributes being built.
                    resolved_values: Mutable resolved value cache used by computed fields.
                """
                object_attributes[key] = self._sanitize_attribute(
                    key,
                    object_attributes[key]
                )
                resolved_values[attr_mapping] = object_attributes[key]

            def _populate_computed_attributes(
                    self,
                    object_attributes,
                    attribute_map,
                    resolved_values
            ):
                """Populate configured computed attributes on a Benchling object.

                Args:
                    object_attributes: Mutable Benchling attributes being built.
                    attribute_map: Benchling-to-STS attribute mapping.
                    resolved_values: Values already resolved from non-computed fields.
                """
                for key, attr_mapping in attribute_map.items():
                    if not self._is_computed_attribute(attr_mapping):
                        continue

                    object_attributes[key] = self._compute_attribute_value(
                        attr_mapping,
                        resolved_values
                    )
                    self._sanitize_resolved_attribute(
                        key,
                        attr_mapping,
                        object_attributes,
                        resolved_values
                    )

            @staticmethod
            def _compute_attribute_value(computed_value_identifier, resolved_values):
                """Compute a configured attribute value from resolved source values.

                Args:
                    computed_value_identifier: Key in COMPUTED_VALUES to evaluate.
                    resolved_values: Values already resolved for the current object.

                Returns:
                    Any: Computed attribute value, falling back to configured default.
                """
                computed_value = factory.COMPUTED_VALUES[factory.mode][
                    computed_value_identifier
                ]
                source_value = resolved_values.get(computed_value['computed_from'])

                return computed_value['values'].get(
                    source_value,
                    computed_value['values']['default']
                )

            def _populate_polymorphic_benchling_relationships(self, sample, object_map):
                """Resolve dynamic relationship aliases into concrete Benchling types.

                Args:
                    sample: STS sample data object used for dynamic type detection.
                    object_map: Object map to mutate with concrete relationship types.
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
                    add_to_return: bool = False,
                    secondary_search_identifier: str = None,
                    secondary_search_value: str = None,
            ) -> str | None:
                """Look up a Benchling object id by search criteria.

                Args:
                    object_type: Benchling object type to search.
                    search_identifier: Primary field or attribute to filter on.
                    search_value: Primary value to match.
                    add_to_return: Whether to append found objects to _return_objects.
                    secondary_search_identifier: Optional secondary schema field.
                    secondary_search_value: Optional secondary value to match.

                Returns:
                    str | None: Benchling object id when found, otherwise None.

                Raises:
                    Exception: If the configured Benchling object type cannot be searched.
                    BenchlingError: If Benchling returns an error other than invalid barcodes.
                """
                filter_object = DataSourceFilter()
                is_barcode_lookup = False
                if 'custom_entity' == factory.benchling.benchling_types[object_type]:
                    schema_filter = DataSourceFilter()
                    schema_filter.and_ = {search_identifier: {'eq': {'value': search_value}}}
                    if secondary_search_identifier and secondary_search_value:
                        schema_filter.and_ = {secondary_search_identifier: {'eq': {'value': secondary_search_value}}}
                    filter_object.and_ = {'schema_fields': schema_filter}
                elif (factory.benchling.benchling_types[object_type]
                      in ['box', 'plate', 'container', 'location']):
                    if 'barcode' == search_identifier:
                        search_identifier = 'barcodes'
                    is_barcode_lookup = search_identifier == 'barcodes'
                    filter_object.and_ = {
                        search_identifier: {'in_list': {'value': [search_value]}}
                    }
                elif factory.benchling.benchling_types[object_type] in ['assay_result']:
                    filter_object.and_ = {'entity_ids': {'in_list': {'value': [search_value]}}}
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
                        self._return_objects.append(
                            self._data_object_factory(
                                object_type,
                                benchling_object.id,
                                attributes=benchling_object.attributes
                            )
                        )

                    return benchling_object.id
                except BenchlingError as exc:
                    if self._is_invalid_barcode_lookup_error(exc, is_barcode_lookup):
                        return None
                    raise
                except StopIteration:
                    return None

            @staticmethod
            def _is_invalid_barcode_lookup_error(exc: BenchlingError, is_barcode_lookup: bool) -> bool:
                """Check whether a Benchling error is an ignorable invalid-barcode lookup.

                Args:
                    exc: Benchling SDK error raised during lookup.
                    is_barcode_lookup: Whether the lookup used the barcode endpoint.

                Returns:
                    bool: True when the error represents invalid barcode input.
                """
                if not is_barcode_lookup:
                    return False
                if getattr(exc, 'status_code', None) != 400:
                    return False

                message = getattr(exc, 'json', None) or getattr(exc, 'message', None)
                if not isinstance(message, dict):
                    return False

                error = message.get('error', {})
                return isinstance(error, dict) and bool(error.get('invalidBarcodes'))

            def _sanitize_attributes(self, object_attributes):
                """Sanitize all values in a Benchling attributes dictionary in place.

                Args:
                    object_attributes: Mutable Benchling attributes to sanitize.
                """
                for key, value in object_attributes.items():
                    object_attributes[key] = self._sanitize_attribute(key, value)

            def _populate_multiselect_benchling_relationships(self, sample, object_map):
                """Populate multiselect Benchling relationship ids on a sample.

                Args:
                    sample: STS sample data object to mutate.
                    object_map: Object map containing multiselect relationship metadata.

                Raises:
                    BenchlingError: If a Benchling relationship lookup fails unexpectedly.
                """
                if 'benchling_multiselect_relationships' in object_map and object_map[
                    'benchling_multiselect_relationships']:
                    for relationship_object_identifier in object_map['benchling_multiselect_relationships']:
                        if (
                            relationship_object_identifier in factory.MULTISELECT_BENCHLING_RELATIONSHIPS[factory.mode] and
                            factory.MULTISELECT_BENCHLING_RELATIONSHIPS[factory.mode][relationship_object_identifier]
                        ):
                            for relationship_object_map in factory.MULTISELECT_BENCHLING_RELATIONSHIPS[factory.mode][relationship_object_identifier].values():
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
                                            object_type=relationship_object_identifier,
                                            search_identifier=relationship_object_map['primary_attribute'],
                                            search_value=search_value,
                                            secondary_search_identifier=relationship_object_map['secondary_attribute'],
                                            secondary_search_value=relationship_object_map['secondary_attribute_value'],
                                        )
                                        if benchling_object_id is not None:
                                            relationship_object_map['stored_values'][search_value] = benchling_object_id

                                    if benchling_object_id is not None:
                                        if not relationship_object_identifier in sample.attributes:
                                            sample.attributes[relationship_object_identifier] = []

                                        if benchling_object_id not in sample.attributes[relationship_object_identifier]:
                                            sample.attributes[relationship_object_identifier].append(
                                                benchling_object_id)

        return StsSampleToCasmBenchlingConverter
