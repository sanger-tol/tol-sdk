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
    rc_barcoding_run_data = RelationshipConfig()
    rc_barcoding_run_data.to_one = {
        'sts_sample': 'sample',
        'sts_specimen': 'specimen',
        'bioscan_specimen': 'specimen',
        'sts_species': 'species'
    }

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
    rc_sample.to_one = {'sts_specimen': 'specimen',
                        'benchling_specimen': 'specimen',
                        'sts_species': 'species',
                        'benchling_species': 'species',
                        'sts_tolid': 'tolid',
                        'benchling_tolid': 'tolid'}
    rc_sample.to_many = {
        'sts_barcoding_run_datas': 'barcoding_run_data',
        'benchling_sequencing_requests': 'sequencing_request',
        'benchling_tissue_preps': 'tissue_prep'
    }
    rc_sample.foreign_keys = {
        'sts_barcoding_run_datas': 'sts_sample.id',
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
        'bioscan_barcoding_run_datas': 'barcoding_run_data',
        'sts_barcoding_run_datas': 'barcoding_run_data'
    }
    rc_specimen.foreign_keys = {
        'benchling_extractions': 'benchling_specimen.id',
        'benchling_samples': 'benchling_specimen.id',
        'benchling_sequencing_request': 'benchling_specimen.id',
        'mlwh_sequencing_request': 'mlwh_specimen.id',
        'sts_samples': 'sts_specimen.id',
        'bioscan_barcoding_run_data': 'bioscan_specimen.id',
        'sts_barcoding_run_data': 'sts_specimen.id'
    }

    rc_species = RelationshipConfig()
    rc_species.to_many = {'sts_samples': 'sample',
                          'benchling_samples': 'sample',
                          'sts_barcoding_run_datas': 'barcoding_run_data',
                          'benchling_tissue_preps': 'tissue_prep',
                          'grit_curations': 'curation'}
    rc_species.foreign_keys = {
        'sts_samples': 'sts_species.id',
        'benchling_samples': 'benchling_species.id',
        'sts_barcoding_run_datas': 'sts_species.id',
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
                           'barcoding_run_data': rc_barcoding_run_data,
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
            }
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
                                                operation='/')
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
