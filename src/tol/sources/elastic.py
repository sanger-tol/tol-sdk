# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
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
    rc_run_data.to_one = {'mlwh_sequencing_request': 'sequencing_request',
                          'mlwh_specimen': 'specimen',
                          'mlwh_species': 'species',
                          'tolqc_sequencing_request': 'sequencing_request',
                          'tolqc_specimen': 'specimen',
                          'tolqc_species': 'species'}

    rc_sequencing_request = RelationshipConfig()
    rc_sequencing_request.to_one = {'benchling_extraction': 'extraction',
                                    'benchling_sample': 'sample',
                                    'benchling_species': 'species'}
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
                            'benchling_species': 'species'}
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
                        'benchling_species': 'species'}
    rc_sample.to_many = {
        'sts_barcoding_run_datas': 'barcoding_run_data',
        'benchling_sequencing_requests': 'sequencing_request'
    }
    rc_sample.foreign_keys = {
        'sts_barcoding_run_datas': 'sts_sample.id',
        'benchling_sequencing_requests': 'benchling_sample.id'
    }

    rc_tolid = RelationshipConfig()
    rc_tolid.to_one = {'informatics_specimen': 'specimen'}

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
                          'sts_barcoding_run_datas': 'barcoding_run_data'}
    rc_species.foreign_keys = {
        'sts_samples': 'sts_species.id',
        'benchling_samples': 'benchling_species.id',
        'sts_barcoding_run_datas': 'sts_species.id'
    }
    relationship_config = {'run_data': rc_run_data,
                           'sequencing_request': rc_sequencing_request,
                           'extraction': rc_extraction,
                           'barcoding_run_data': rc_barcoding_run_data,
                           'sample': rc_sample,
                           'tolid': rc_tolid,
                           'specimen': rc_specimen,
                           'species': rc_species}
    elastic = ElasticDataSource({'uri': os.getenv('ELASTIC_URI'),
                                 'user': os.getenv('ELASTIC_USER'),
                                 'password': os.getenv('ELASTIC_PASSWORD'),
                                 'index_prefix': os.getenv('ELASTIC_INDEX_PREFIX'),
                                 'relationship_cfg': relationship_config})
    core_data_object(elastic)
    return elastic
