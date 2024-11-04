# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .portal_attributes import portal_attributes
from ..core import (
    core_data_object
)
from ..core.data_source_attribute_metadata import data_source_attribute_metadata
from ..core.relationship import RelationshipConfig
from ..elastic import (
    ElasticDataSource,
    RuntimeFields
)


def elastic():
    rc_run_data = RelationshipConfig()
    rc_run_data.to_one = {'benchling_extraction': 'extraction',
                          'benchling_sample': 'sample',
                          'mlwh_sequencing_request': 'sequencing_request',
                          'mlwh_specimen': 'specimen',
                          'mlwh_species': 'species',
                          'mlwh_tolid': 'tolid',
                          'tolqc_sequencing_request': 'sequencing_request',
                          'tolqc_specimen': 'specimen',
                          'tolqc_species': 'species',
                          'tolqc_tolid': 'tolid'}

    rc_sequencing_request = RelationshipConfig()
    rc_sequencing_request.to_one = {'benchling_extraction': 'extraction',
                                    'benchling_sample': 'sample',
                                    'benchling_species': 'species',
                                    'benchling_tolid': 'tolid',
                                    'benchling_specimen': 'specimen',
                                    'benchling_tissue_prep': 'tissue_prep',
                                    'mlwh_species': 'species',
                                    'mlwh_tolid': 'tolid',
                                    'mlwh_specimen': 'specimen'}
    rc_sequencing_request.to_many = {
        'mlwh_run_datas': 'run_data',
        'tolqc_run_datas': 'run_data'
    }
    rc_sequencing_request.foreign_keys = {
        'mlwh_run_datas': 'mlwh_sequencing_request.id',
        'tolqc_run_datas': 'tolqc_sequencing_request.id'
    }

    rc_extraction = RelationshipConfig()
    rc_extraction.to_one = {'benchling_sample': 'sample',
                            'benchling_species': 'species',
                            'benchling_specimen': 'specimen',
                            'benchling_tolid': 'tolid',
                            'benchling_tissue_prep': 'tissue_prep'}
    rc_extraction.to_many = {
        'benchling_sequencing_requests': 'sequencing_request'
    }
    rc_extraction.foreign_keys = {
        'benchling_sequencing_request': 'benchling_extraction.id'
    }

    rc_sample = RelationshipConfig()
    rc_sample.to_one = {
        'sts_specimen': 'specimen',
        'benchling_specimen': 'specimen',
        'sts_species': 'species',
        'benchling_species': 'species',
        'sts_tolid': 'tolid',
        'tolid_tolid': 'tolid',
        'benchling_tolid': 'tolid',
        'sts_manifest': 'manifest',
        'sts_sampleset': 'sampleset'
    }
    rc_sample.to_many = {
        'benchling_sequencing_requests': 'sequencing_request',
        'benchling_tissue_preps': 'tissue_prep'
    }
    rc_sample.foreign_keys = {
        'benchling_sequencing_requests': 'benchling_sample.id',
        'benchling_tissue_preps': 'benchling_sample.id'
    }

    rc_sampleset = RelationshipConfig()
    rc_sampleset.to_one = {}
    rc_sampleset.to_many = {
        'sts_manifests': 'manifest',
        'sts_samples': 'sample'
    }
    rc_sampleset.foreign_keys = {
        'sts_manifests': 'sts_sampleset.id',
        'sts_samples': 'sts_sampleset.id'
    }

    rc_manifest = RelationshipConfig()
    rc_manifest.to_one = {
        'sts_sampleset': 'sampleset'
    }
    rc_manifest.to_many = {'sts_samples': 'sample'}
    rc_manifest.foreign_keys = {
        'sts_samples': 'sts_manifest.id'
    }

    rc_tolid = RelationshipConfig()
    rc_tolid.to_one = {'informatics_specimen': 'specimen',
                       'tolid_specimen': 'specimen',
                       'tolid_species': 'species'}
    rc_tolid.to_many = {
        'benchling_tissue_preps': 'tissue-prep',
        'grit_curations': 'curation'
    }
    rc_tolid.foreign_keys = {
        'benchling_tissue_preps': 'benchling_tolid.id',
        'grit_curations': 'grit_tolid.id'
    }

    rc_specimen = RelationshipConfig()
    rc_specimen.to_many = {
        'benchling_extractions': 'extraction',
        'benchling_samples': 'sample',
        'benchling_sequencing_request': 'sequencing_request',
        'mlwh_sequencing_request': 'sequencing_request',
        'sts_samples': 'sample',
    }
    rc_specimen.foreign_keys = {
        'benchling_extractions': 'benchling_specimen.id',
        'benchling_samples': 'benchling_specimen.id',
        'benchling_sequencing_request': 'benchling_specimen.id',
        'mlwh_sequencing_request': 'mlwh_specimen.id',
        'sts_samples': 'sts_specimen.id',
    }

    rc_species = RelationshipConfig()
    rc_species.to_many = {'sts_samples': 'sample',
                          'benchling_samples': 'sample',
                          'benchling_tissue_preps': 'tissue_prep',
                          'grit_curations': 'curation'}
    rc_species.foreign_keys = {
        'sts_samples': 'sts_species.id',
        'benchling_samples': 'benchling_species.id',
        'benchling_tissue_preps': 'benchling_species.id',
        'grit_curations': 'grit_species.id'
    }

    rc_tissue_prep = RelationshipConfig()
    rc_tissue_prep.to_one = {'benchling_species': 'species',
                             'benchling_sample': 'sample',
                             'benchling_specimen': 'specimen',
                             'benchling_tolid': 'tolid'}
    rc_tissue_prep.to_many = {
        'benchling_extractions': 'extraction',
        'benchling_sequencing_requests': 'sequencing_request',
        'benchling_tissue_preps': 'tissue_prep'
    }
    rc_tissue_prep.foreign_keys = {
        'benchling_extractions': 'benchling_tissue_prep.id',
        'benchling_sequencing_requests': 'benchling_tissue_prep.id',
        'benchling_tissue_preps': 'benchling_tissue_prep.id'
    }

    rc_curation = RelationshipConfig()
    rc_curation.to_one = {'grit_species': 'species',
                          'grit_tolid': 'tolid'}

    relationship_config = {'run_data': rc_run_data,
                           'sequencing_request': rc_sequencing_request,
                           'extraction': rc_extraction,
                           'sample': rc_sample,
                           'sampleset': rc_sampleset,
                           'manifest': rc_manifest,
                           'tolid': rc_tolid,
                           'specimen': rc_specimen,
                           'species': rc_species,
                           'tissue_prep': rc_tissue_prep,
                           'curation': rc_curation}

    runtime_fields = {
        'species': {
            'calc_done_date': {
                'type': 'date',
                'script': """
                    if (doc['mlwh_run_data_mlwh_run_complete_rnaseq_min'].size() > 0
                        && doc['informatics_tolid_informatics_status_summary_min.keyword'].size()
                            > 0
                        && doc['informatics_tolid_informatics_status_summary_min.keyword'].value
                            == '1 submitted') {
                            emit(doc['mlwh_run_data_mlwh_run_complete_rnaseq_min']
                                .value.toEpochMilli())
                    }
                """
            },
            'calc_pm_status': {
                'type': 'keyword',
                'script': {
                    'source': """
                    def statusMapping = [
                        '11_published': '1. Submitted', '12_public': '1. Submitted',
                        '13_submitted': '1. Submitted',
                        '21_in_submission': '2. Curated', '22_postprocessing': '2. Curated',
                        '23_submission_hold': '2. Curated',
                        '31_curation': '3. In curation', '33_build': '3. In curation',
                        '34_contam_check': '3. In curation','34_contam_check_btk':
                        '3. In curation', '35_open': '3. In curation', 
                        '36_awaiting_data': '3. In curation',
                        '41_data_asm': '4. In Assembly', '42_asm_r&d': '4. In Assembly',
                        '43_hold_for_analysis': '4. In Assembly', '44_faculty_asm':
                        '4. In Assembly', '44_awaiting_new_data' : '4. In Assembly',
                        '45_resubmit_asm': '4. In Assembly',
                        '46_faculty_asm': '4. In Assembly', '51_pacbio_fail':
                        '5. In Sequencing', '52_hic_fail': '5. In Sequencing',
                        '54_species_id': '5. In Sequencing', '55_data_query':
                        '5. In Sequencing','56_data_wrangle': '5. In Sequencing',
                        '61_lr_asm_10x': '5. In Sequencing','62_lr_asm':
                        '5. In Sequencing', '63_lr_topup_hic': '5. In Sequencing',
                        '63_lr_topup': '5. In Sequencing','64_10x_only':
                        '5. In Sequencing', '64_10x_hic_only': '5. In Sequencing',
                        '65_hic_only': '5. In Sequencing', '66_rnaseq_only':
                        '5. In Sequencing'
                    ];
                    if (doc['informatics_tolid_informatics_status_min.keyword'].size() > 0) {
                        def status = doc['informatics_tolid_informatics_status_min.keyword'].value;
                        if (statusMapping.containsKey(status)) {
                            emit(statusMapping[status]);
                        }
                    } else if (doc.containsKey('sts_sample_sts_tollab_assign_date_min')) {
                        if (doc['sts_sample_sts_tollab_assign_date_min'].size() > 0) {
                            emit("6. Sent to lab");
                        } else {
                            emit("7. Onboarding");
                        }
                    }
                """
                }
            },
        },
        'specimen': {
            'calc_coverage_post_run': RuntimeFields.math(
                'mlwh_run_data_mlwh_hifi_read_bases_sum',
                'sts_estimated_genome_size',
                operation='/'
            )
        },
        'tolid': {
            'calc_coverage': RuntimeFields.math('mlwh_run_data_mlwh_hifi_read_bases_sum',
                                                'tolid_species.sts_genome_size',
                                                operation='/'),
        },
        'sample': {
            'calc_biospecimen_id':
                RuntimeFields.coalesce([
                    'sts_sample_same_as',
                    'sts_biospecimen_accession',
                    'sts_sample_symbiont_of'
                ])
        },
        'sampleset': {
            'calc_tat': RuntimeFields.date_interval('sts_submit_date',
                                                    'sts_sample_sts_receive_date_min',
                                                    'days')
        },
        'manifest': {
            'calc_tat': RuntimeFields.date_interval('sts_submit_date',
                                                    'sts_receive_date',
                                                    'days')
        },
        'sequencing_request': {
            'calc_existing_library_oplc': {
                'type': 'double',
                'script': {
                    'source': """
                      if (doc.containsKey('mlwh_insert_size')
                      && doc['mlwh_insert_size'].size() > 0
                      && doc.containsKey('mlwh_concentration')
                      && doc['mlwh_concentration'].size() > 0
                      && doc.containsKey('mlwh_volume_remaining')
                      && doc['mlwh_volume_remaining'].size() > 0){
                        emit((doc['mlwh_concentration']
                        .value/(doc['mlwh_insert_size'].value * 660))
                        * doc['mlwh_volume_remaining'].value * 7500000)
                }
                """
                }
            }
        }
    }

    amd = data_source_attribute_metadata(
        portal_attributes()
    )

    elastic = ElasticDataSource({
        'uri': os.getenv('ELASTIC_URI'),
        'user': os.getenv('ELASTIC_USER'),
        'password': os.getenv('ELASTIC_PASSWORD'),
        'index_prefix': os.getenv('ELASTIC_INDEX_PREFIX'),
        'relationship_cfg': relationship_config,
        'runtime_fields': runtime_fields},
        attribute_metadata=amd)
    core_data_object(elastic)
    return elastic
