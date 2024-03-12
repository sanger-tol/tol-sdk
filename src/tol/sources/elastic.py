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
    ElasticDataSource
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
                                    'mlwh_species': 'species',
                                    'mlwh_tolid': 'tolid'}
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

    rc_tolid = RelationshipConfig()
    rc_tolid.to_one = {'informatics_specimen': 'specimen',
                       'tolid_specimen': 'specimen',
                       'tolid_species': 'species'}
    rc_tolid.to_many = {'benchling_tissue_preps': 'tissue-prep'}
    rc_tolid.foreign_keys = {
        'benchling_tissue_preps': 'benchling_tolid.id'
    }

    rc_specimen = RelationshipConfig()
    rc_specimen.to_many = {
        'benchling_samples': 'sample',
        'sts_samples': 'sample',
        'bioscan_barcoding_run_datas': 'barcoding_run_data',
        'sts_barcoding_run_datas': 'barcoding_run_data'
    }
    rc_specimen.foreign_keys = {
        'benchling_samples': 'benchling_specimen.id',
        'sts_samples': 'sts_specimen.id',
        'bioscan_barcoding_run_data': 'bioscan_specimen.id',
        'sts_barcoding_run_data': 'sts_specimen.id'
    }

    rc_species = RelationshipConfig()
    rc_species.to_many = {'sts_samples': 'sample',
                          'benchling_samples': 'sample',
                          'sts_barcoding_run_datas': 'barcoding_run_data',
                          'benchling_tissue_preps': 'tissue_prep'}
    rc_species.foreign_keys = {
        'sts_samples': 'sts_species.id',
        'benchling_samples': 'benchling_species.id',
        'sts_barcoding_run_datas': 'sts_species.id',
        'benchling_tissue_preps': 'benchling_species.id'
    }

    rc_tissue_prep = RelationshipConfig()
    rc_tissue_prep.to_one = {'benchling_species': 'species',
                             'benchling_sample': 'sample',
                             'benchling_tolid': 'tolid'}
    rc_tissue_prep.to_many = {
        'benchling_extractions': 'extraction'
    }
    rc_tissue_prep.foreign_keys = {
        'benchling_extractions': 'benchling_tissue_prep.id'
    }

    relationship_config = {'run_data': rc_run_data,
                           'sequencing_request': rc_sequencing_request,
                           'extraction': rc_extraction,
                           'barcoding_run_data': rc_barcoding_run_data,
                           'sample': rc_sample,
                           'tolid': rc_tolid,
                           'specimen': rc_specimen,
                           'species': rc_species,
                           'tissue_prep': rc_tissue_prep}

    runtime_fields = {
        'species': {
            'calc_coverage': {
                'type': 'double',
                'script': """
                    if (doc['mlwh_run_data_mlwh_hifi_read_bases_sum'].size() > 0
                        && doc['sts_genome_size'].size() > 0) {
                        emit(doc['mlwh_run_data_mlwh_hifi_read_bases_sum'].value /
                             doc['sts_genome_size'].value)
                    }
                """
            }
        },
        'tolid': {
            'calc_coverage': {
                'type': 'double',
                'script': """
                    if (doc['mlwh_run_data_mlwh_hifi_read_bases_sum'].size() > 0
                        && doc['tolid_species.sts_genome_size'].size() > 0) {
                        emit(doc['mlwh_run_data_mlwh_hifi_read_bases_sum'].value /
                             doc['tolid_species.sts_genome_size'].value)
                    }
                """
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
