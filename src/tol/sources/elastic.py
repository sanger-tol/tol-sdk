# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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
    RuntimeField,
    RuntimeFields
)


def elastic(
        environment: str = None,
        product: str = None,
        **kwargs
) -> ElasticDataSource:
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
                                    'mlwh_specimen': 'specimen',
                                    'mlwh_sample': 'sample'}
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
        'grit_curations': 'curation',
        'gap_assemblies': 'assembly',
        'gn_genome_notes': 'genome_note'
    }
    rc_tolid.foreign_keys = {
        'benchling_tissue_preps': 'benchling_tolid.id',
        'grit_curations': 'grit_tolid.id',
        'gap_assemblies': 'gap_tolid.id',
        'gn_genome_notes': 'gn_tolid.id'
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
                          'grit_curations': 'curation',
                          'gap_assemblies': 'assembly',
                          'gn_genome_notes': 'genome_note'}
    rc_species.foreign_keys = {
        'sts_samples': 'sts_species.id',
        'benchling_samples': 'benchling_species.id',
        'benchling_tissue_preps': 'benchling_species.id',
        'grit_curations': 'grit_species.id',
        'gap_assemblies': 'gap_species.id',
        'gn_genome_notes': 'gn_species.id'
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

    rc_assembly = RelationshipConfig()
    rc_assembly.to_one = {'gap_species': 'species'}
    rc_assembly.to_many = {
        'gn_genome_notes': 'genome_note',
        'gap_assembly_analyses': 'assembly_analysis'
    }
    rc_assembly.foreign_keys = {
        'gn_genome_notes': 'gn_assembly.id',
        'gap_assembly_analyses': 'gap_assembly.id'
    }

    rc_assembly_analysis = RelationshipConfig()
    rc_assembly_analysis.to_one = {
        'gap_species': 'species',
        'gap_assembly': 'assembly'
    }

    rc_genome_note = RelationshipConfig()
    rc_genome_note.to_one = {
        'gn_assembly': 'assembly',
        'gn_species': 'species',
        'gn_tolid': 'tolid'
    }

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
                           'curation': rc_curation,
                           'assembly': rc_assembly,
                           'assembly_analysis': rc_assembly_analysis,
                           'genome_note': rc_genome_note}

    runtime_fields = {
        'species': {
            'calc_done_date': RuntimeFields.latest_date(
                [
                    'mlwh_run_data_mlwh_run_complete_rnaseq_min',
                    'grit_curation_grit_in_submission_date_min'
                ],
                allow_missing=False
            ),
            'calc_is_novel': RuntimeField(
                field_type='boolean',
                dependencies=['sts_species_id'],
                function_body="""
                    emit(!(doc.containsKey('sts_sample_sts_tollab_assign_date_min')
                        && doc['sts_sample_sts_tollab_assign_date_min'].size() > 0))
                """,
                function_default='emit(false)'
            ).to_dict(),
            'calc_pm_status': {
                'type': 'keyword',
                'script': {
                    'source': """
                        String status = null;
                        if (doc.containsKey
                            ('informatics_tolid_informatics_status_summary_min.keyword')
                            && doc['informatics_tolid_informatics_status_summary_min.keyword']
                            .size() > 0) {
                            status =
                            doc['informatics_tolid_informatics_status_summary_min.keyword'].value;
                        }

                        String stage = null;
                        if (doc.containsKey('tolqclegacy_assembly_stage.keyword')
                            && doc['tolqclegacy_assembly_stage.keyword'].size() > 0) {
                            stage = doc['tolqclegacy_assembly_stage.keyword'].value;
                        }

                        boolean onSite = doc.containsKey('sts_sample_sts_receive_date_max')
                        && doc['sts_sample_sts_receive_date_max'].size() > 0;

                        boolean releasedToLab =
                        doc.containsKey('sts_sample_sts_tollab_assign_date_min')
                        && doc['sts_sample_sts_tollab_assign_date_min'].size() > 0;

                        boolean noDataYet =
                        (status == null)
                        && (stage == null || stage == '-')
                        && doc.containsKey('mlwh_run_data_mlwh_run_complete_pacbio_min')
                        && doc['mlwh_run_data_mlwh_run_complete_pacbio_min'].size() == 0
                        && doc.containsKey('mlwh_run_data_mlwh_run_complete_hic_min')
                        && doc['mlwh_run_data_mlwh_run_complete_hic_min'].size() == 0;

                        boolean submitted = status == '1 submitted' && stage == 'RELEASED';

                        boolean curation = status == '2 curated' || status == '3 curation';

                        boolean dataComplete = status == '4 data complete';

                        boolean dataIssue = status == '5 data issue';

                        boolean dataGeneration = status == '6 data generation';

                        if (onSite) {
                            emit('a. Species on site');

                            if (!releasedToLab) {
                                emit('b. Not released to lab');
                            } else {
                                if (noDataYet) {
                                    emit('c. No data yet');
                                }
                                if (dataGeneration) {
                                    emit('d. Data generation');
                                }
                                if (dataIssue) {
                                    emit('e. Data issue');
                                }
                                if (dataComplete) {
                                    emit('f. Data complete');
                                }
                                if (curation) {
                                    emit('g. Curation');
                                }
                                if (submitted) {
                                    emit('h. Submitted');
                                }
                            }
                        } else {
                            emit('i. Species not on site');
                        }
                    """
                }
            },
            'calc_specimen_needed_at_sanger_psyche': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean isRecollectionRequired = (
                            doc.containsKey('sts_sequencing_material_status.keyword') &&
                            doc['sts_sequencing_material_status.keyword'].size() > 0 &&
                            doc['sts_sequencing_material_status.keyword'].value
                            == 'RECOLLECTION_REQUIRED'
                        );

                        boolean isIncludedProject = (
                            doc.containsKey('goat_long_list.keyword') &&
                            doc['goat_long_list.keyword'].size() > 0 &&
                            ['AG100PEST', 'i5K', 'CBP', 'ERGA-PIL', 'ERGA-BGE', 'ERGA-CH',
                            'ENDEMIXIT'].contains(doc['goat_long_list.keyword'].value)
                        );

                        boolean isChromosome = (
                            doc.containsKey('goat_assembly_level.keyword') &&
                            doc['goat_assembly_level.keyword'].size() > 0 &&
                            doc['goat_assembly_level.keyword'].value == 'Chromosome'
                        );

                        boolean isSpecimensAtSanger = (
                            doc.containsKey('tolid_tolid_count') &&
                            doc['tolid_tolid_count'].size() > 0
                        );

                        emit(
                            isRecollectionRequired || (!isIncludedProject
                            && !isChromosome && !isSpecimensAtSanger)
                        );
                    """
                }
            },
            'calc_specimen_collection_needed_psyche': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean isRecollectionRequired = (
                            doc.containsKey('sts_sequencing_material_status.keyword') &&
                            doc['sts_sequencing_material_status.keyword'].size() > 0 &&
                            doc['sts_sequencing_material_status.keyword'].value
                            == 'RECOLLECTION_REQUIRED'
                        );

                        boolean isIncludedProject = (
                            doc.containsKey('goat_long_list.keyword') &&
                            doc['goat_long_list.keyword'].size() > 0 &&
                            ['AG100PEST', 'i5K', 'CBP', 'ERGA-PIL', 'ERGA-BGE', 'ERGA-CH',
                            'ENDEMIXIT'].contains(doc['goat_long_list.keyword'].value)
                        );

                        boolean isChromosome = (
                            doc.containsKey('goat_assembly_level.keyword') &&
                            doc['goat_assembly_level.keyword'].size() > 0 &&
                            doc['goat_assembly_level.keyword'].value == 'Chromosome'
                        );

                        boolean isSpecimensAtSanger = (
                            doc.containsKey('tolid_tolid_count') &&
                            doc['tolid_tolid_count'].size() > 0
                        );

                        boolean isSampleCollectedForPsyche = false;
                        if (doc.containsKey('goat_sample_collected.keyword') &&
                            doc['goat_sample_collected.keyword'].size() > 0) {
                            for (String value : doc['goat_sample_collected.keyword']) {
                                if (value != null && value.contains('PSYCHE')) {
                                    isSampleCollectedForPsyche = true;
                                    break;
                                }
                            }
                        }

                        emit(
                            isRecollectionRequired || (!isIncludedProject
                            && !isChromosome && !isSpecimensAtSanger
                            && !isSampleCollectedForPsyche)
                        );
                    """
                }
            },
            'calc_species_epithet': {
                'type': 'keyword',
                'script': {
                    'source': """
                        String result = "";
                        if (doc.containsKey('goat_species_name.keyword')) {
                            def values = doc['goat_species_name.keyword'];
                            if (values.size() > 0) {
                                String fullName = values.value;
                                int firstSpace = fullName.indexOf(' ');
                                if (firstSpace > 0 && firstSpace < fullName.length() - 1) {
                                    int secondSpace = fullName.indexOf(' ', firstSpace + 1);
                                    if (secondSpace > 0) {
                                        result = fullName.substring(firstSpace + 1, secondSpace);
                                    } else {
                                        result = fullName.substring(firstSpace + 1);
                                    }
                                }
                            }
                        }
                        emit(result);
                    """
                }
            },
            'calc_recollection_needed': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean isTopUpCountZero = (
                            (!doc.containsKey('calc_topup_required_tolid_count') ||
                            doc['calc_topup_required_tolid_count'].size() == 0) ||
                            (doc.containsKey('calc_topup_required_tolid_count') &&
                            doc['calc_topup_required_tolid_count'].size() > 0 &&
                            doc['calc_topup_required_tolid_count'].value == 0)
                        );

                        boolean isIndividualExhaustedCountZero = (
                            (!doc.containsKey('calc_individual_exhausted_tolid_count') ||
                            doc['calc_individual_exhausted_tolid_count'].size() == 0) ||
                            (doc.containsKey('calc_individual_exhausted_tolid_count') &&
                            doc['calc_individual_exhausted_tolid_count'].size() > 0 &&
                            doc['calc_individual_exhausted_tolid_count'].value == 0)
                        );

                        boolean isIndividualNovel =
                        (
                            isTopUpCountZero && isIndividualExhaustedCountZero
                        );

                        boolean isAllTopUpRequired = (
                            doc.containsKey('calc_tolid_calc_topup_required_min') &&
                            doc['calc_tolid_calc_topup_required_min'].size() > 0 &&
                            doc['calc_tolid_calc_topup_required_min'].value == 1
                        );

                        boolean isAllIndividualsExhausted = (
                            doc.containsKey('calc_tolid_calc_individual_exhausted_min') &&
                            doc['calc_tolid_calc_individual_exhausted_min'].size() > 0 &&
                            doc['calc_tolid_calc_individual_exhausted_min'].value == 1
                        );

                        boolean isRecollectionNeeded = (
                            ((!doc.containsKey('calc_individual_exhausted_tolid_count')
                            || doc['calc_individual_exhausted_tolid_count'].size() == 0)
                            && (!doc.containsKey('tolid_tolid_count') ||
                            doc['tolid_tolid_count'].size() == 0)) ||
                            (doc.containsKey('calc_individual_exhausted_tolid_count') &&
                            doc.containsKey('tolid_tolid_count') &&
                            doc['calc_individual_exhausted_tolid_count'].size() > 0 &&
                            doc['tolid_tolid_count'].size() > 0 &&
                            doc['calc_individual_exhausted_tolid_count'].value
                            - doc['tolid_tolid_count'].value == 0)
                        );

                        emit(
                            !isIndividualNovel && isAllTopUpRequired
                            && isAllIndividualsExhausted && isRecollectionNeeded
                        );
                    """
                }
            },
            'calc_species_out_for_recollection': {
                'type': 'boolean',
                'script': {
                    'source': """
                        if (doc.containsKey('portaldb_date_marked_for_recollection') &&
                            doc['portaldb_date_marked_for_recollection'].size() > 0) {
                            if (doc.containsKey('sts_sample_sts_submit_date_max') &&
                                doc['sts_sample_sts_submit_date_max'].size() > 0 &&
                                doc['portaldb_date_marked_for_recollection'].value.isBefore(
                                doc['sts_sample_sts_submit_date_max'].value)) {
                                    emit (false);
                            } else {
                                emit (true);
                            }
                        } else {
                            emit (false);
                        }
                    """
                }
            },
            'calc_no_null_tolid_tolid_count': {
                'type': 'double',
                'script': {
                    'source': """

                        boolean isThereAValueNonNull = (
                            doc.containsKey('tolid_tolid_count') &&
                            doc['tolid_tolid_count'].size() > 0 &&
                            doc['tolid_tolid_count']
                            .value != null
                        );

                        if (isThereAValueNonNull) {
                            emit(doc['tolid_tolid_count'].value);
                        } else {
                            emit(0.0);
                        }
                    """
                }
            }
        },
        'specimen': {
            'calc_coverage_post_run': RuntimeFields.math(
                'tolqc_run_data_tolqc_bases_pacbio_sum',
                'sts_estimated_genome_size',
                operation='/'
            )
        },
        'tolid': {
            'calc_coverage': RuntimeFields.math('tolqc_run_data_tolqc_bases_pacbio_sum',
                                                'tolid_species.sts_genome_size',
                                                operation='/'),
            'calc_ongoing_submissions': RuntimeFields.math(
                'benchling_pacbio_sequencing_request_count',
                'benchling_pacbio_completed_sequencing_request_count',
                operation='-'),
            'calc_coverage_met': {
                'type': 'boolean',
                'script': {
                    'source': """
                        if (doc.containsKey('tolqc_run_data_tolqc_bases_pacbio_sum') &&
                        doc.containsKey('tolid_species.sts_genome_size') &&
                        doc.containsKey('sts_sample_sts_target_coverage_max') &&
                        doc['tolqc_run_data_tolqc_bases_pacbio_sum'].size() > 0 &&
                        doc['tolid_species.sts_genome_size'].size() > 0 &&
                        doc['sts_sample_sts_target_coverage_max'].size() > 0) {
                            emit(doc['tolqc_run_data_tolqc_bases_pacbio_sum'].value /
                                doc['tolid_species.sts_genome_size'].value >=
                                doc['sts_sample_sts_target_coverage_max'].value)
                        }
                        else {
                            emit(false)
                        }
                    """
                }
            },
            'calc_topup_required': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean allRequiredFieldsPresent = (
                            doc.containsKey('benchling_pacbio_sequencing_request_count') &&
                            doc['benchling_pacbio_sequencing_request_count'].size() > 0 &&
                            doc.containsKey(
                                'benchling_pacbio_completed_sequencing_request_count'
                            ) &&
                            doc[
                                'benchling_pacbio_completed_sequencing_request_count'
                            ].size() > 0 &&
                            doc.containsKey('tolqc_run_data_tolqc_bases_pacbio_sum') &&
                            doc['tolqc_run_data_tolqc_bases_pacbio_sum'].size() > 0 &&
                            doc.containsKey('tolid_species.sts_genome_size') &&
                            doc['tolid_species.sts_genome_size'].size() > 0 &&
                            doc.containsKey('sts_sample_sts_target_coverage_max') &&
                            doc['sts_sample_sts_target_coverage_max'].size() > 0
                        );

                        if (!allRequiredFieldsPresent) {
                            emit(false);
                            return;
                        }

                        boolean isInReview =
                            doc.containsKey('portaldb_in_review') &&
                            doc['portaldb_in_review'].size() > 0 &&
                            doc['portaldb_in_review'].value == true;

                        boolean isTotalSubmissionsGreaterThanZero =
                            doc['benchling_pacbio_sequencing_request_count'].value > 0;

                        boolean isOngoingSubmissionsEqualZero =
                            ((!doc.containsKey('benchling_pacbio_sequencing_request_count') ||
                            doc['benchling_pacbio_sequencing_request_count'].size() == 0) &&
                            (!doc.containsKey('benchling_pacbio_completed_sequencing_request_count')
                            || doc['benchling_pacbio_completed_sequencing_request_count']
                            .size() == 0)) ||
                            (doc.containsKey('benchling_pacbio_sequencing_request_count') &&
                            doc.containsKey('benchling_pacbio_completed_sequencing_request_count')
                            && doc['benchling_pacbio_sequencing_request_count'].size() > 0 &&
                            doc['benchling_pacbio_completed_sequencing_request_count'].size() > 0
                            && doc['benchling_pacbio_sequencing_request_count'].value -
                            doc['benchling_pacbio_completed_sequencing_request_count'].value == 0);

                        boolean isTargetCoverageMet =
                            (doc['tolqc_run_data_tolqc_bases_pacbio_sum'].value /
                            doc['tolid_species.sts_genome_size'].value >=
                            doc['sts_sample_sts_target_coverage_max'].value);

                        boolean isSpecimenNotAtSequencingStage = false;

                        String statusField =
                        'tolid_species.informatics_tolid_informatics_status_summary_min.keyword';

                        if (doc.containsKey(statusField) &&
                            doc[statusField].size() > 0) {

                            for (String value : doc[statusField]) {
                                if (value == '1 submitted' ||
                                    value == '2 curated' ||
                                    value == '3 curation' ||
                                    value == '4 data complete' ||
                                    value == '7 ignore') {
                                    isSpecimenNotAtSequencingStage = true;
                                    break;
                                }
                            }
                        }

                        emit(
                            isTotalSubmissionsGreaterThanZero &&
                            isOngoingSubmissionsEqualZero &&
                            !isTargetCoverageMet &&
                            !isSpecimenNotAtSequencingStage &&
                            !isInReview
                        );
                    """
                }
            },
            'calc_tolid_actionable': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean result = false;

                        boolean isTolidNotBeenActioned = (
                            !doc.containsKey('portaldb_date_topup_actioned') ||
                            doc['portaldb_date_topup_actioned'].size() == 0 ||
                            doc['portaldb_date_topup_actioned'].value == null
                        );

                        if (isTolidNotBeenActioned) {
                            result = true;
                        }
                        else if (doc.containsKey('mlwh_run_data_mlwh_run_complete_max') &&
                                doc['mlwh_run_data_mlwh_run_complete_max'].size() > 0) {

                            result = doc['portaldb_date_topup_actioned'].value.isBefore(
                                doc['mlwh_run_data_mlwh_run_complete_max'].value);
                        }

                        emit(result);
                    """
                }
            },
            'calc_individual_exhausted': {
                'type': 'boolean',
                'script': {
                    'source': """
                        def benchlingNewSampleCount = 0;
                        if (doc.containsKey('benchling_sample_count')
                          && doc['benchling_sample_count'].size() > 0) {
                          benchlingNewSampleCount = doc['benchling_sample_count'].value;
                        }
                        def abandonCnt = 0;
                        if (doc.containsKey('calc_sample_calc_sample_abandoned_in_sts_count')
                          && doc['calc_sample_calc_sample_abandoned_in_sts_count'].size() > 0) {
                          abandonCnt = doc['calc_sample_calc_sample_abandoned_in_sts_count'].value;
                        }

                        def totalSampleCount = benchlingNewSampleCount + abandonCnt;

                        boolean allSamplesAccountedFor = false;
                        if (doc.containsKey('sts_sample_count') &&
                          doc['sts_sample_count'].size() > 0 &&
                          totalSampleCount == doc['sts_sample_count'].value) {
                          allSamplesAccountedFor = true;
                        }

                        boolean allBenchlingMaterialExhausted = false;
                        if (
                          benchlingNewSampleCount > 0 &&
                          doc.containsKey('calc_sequencing_request_calc_mlwh_volume_remaining_max')
                          &&
                          doc.containsKey('calc_extraction_calc_benchling_volume_ul_dna_max') &&
                          doc.containsKey('calc_tissue_prep_calc_benchling_weight_mg_max') &&
                          doc.containsKey('calc_sample_calc_benchling_remaining_weight_max') &&
                          doc['calc_sequencing_request_calc_mlwh_volume_remaining_max'].size() > 0
                          &&
                          doc['calc_extraction_calc_benchling_volume_ul_dna_max'].size() > 0 &&
                          doc['calc_tissue_prep_calc_benchling_weight_mg_max'].size() > 0 &&
                          doc['calc_sample_calc_benchling_remaining_weight_max'].size() > 0 &&
                          doc['calc_sequencing_request_calc_mlwh_volume_remaining_max'].value <= 0
                          &&
                          doc['calc_extraction_calc_benchling_volume_ul_dna_max'].value <= 0 &&
                          doc['calc_tissue_prep_calc_benchling_weight_mg_max'].value <= 0 &&
                          doc['calc_sample_calc_benchling_remaining_weight_max'].value <= 0
                        ) {
                          allBenchlingMaterialExhausted = true;
                        }

                        emit(allSamplesAccountedFor &&
                          (benchlingNewSampleCount == 0 || allBenchlingMaterialExhausted));
                    """
                }
            },
            'calc_individual_available': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean isThereAtLeastAnotherIndividual = (
                            doc.containsKey('tolid_species.tolid_tolid_count') &&
                            doc['tolid_species.tolid_tolid_count'].size() > 0 &&
                            doc['tolid_species.tolid_tolid_count'].value > 1
                        );

                         boolean isAtLeastOneIndividualExhausted = (
                            doc.containsKey
                            ('tolid_species.calc_tolid_calc_individual_exhausted_max') &&
                            doc['tolid_species.calc_tolid_calc_individual_exhausted_max']
                            .size() > 0 &&
                            doc['tolid_species.calc_tolid_calc_individual_exhausted_max']
                            .value == 1

                        );

                        boolean isSpeciesTopUpEqualsIndividualExhausted = (
                            ((!doc.containsKey('tolid_species.calc_topup_required_tolid_count') ||
                            doc['tolid_species.calc_topup_required_tolid_count'].size() == 0) &&
                            (!doc.containsKey(
                            'tolid_species.calc_individual_exhausted_tolid_count') ||
                            doc['tolid_species.calc_individual_exhausted_tolid_count']
                            .size() == 0)) ||
                            (doc.containsKey('tolid_species.calc_topup_required_tolid_count') &&
                            doc.containsKey('tolid_species.calc_individual_exhausted_tolid_count')
                            && doc['tolid_species.calc_topup_required_tolid_count']
                            .size() > 0 &&
                            doc['tolid_species.calc_individual_exhausted_tolid_count']
                            .size() > 0 &&
                            doc['tolid_species.calc_topup_required_tolid_count'].value -
                            doc['tolid_species.calc_individual_exhausted_tolid_count']
                            .value == 0)
                        );

                        boolean isSpecimenNotAtSequencingStage = false;

                        if (doc.containsKey('informatics_status_summary.keyword') &&
                            doc['informatics_status_summary.keyword'].size() > 0) {

                            for (String value : doc['informatics_status_summary.keyword']) {
                                if (value == '1 submitted' ||
                                    value == '2 curated' ||
                                    value == '3 curation' ||
                                    value == '4 data complete' ||
                                    value == '7 ignore') {
                                    isSpecimenNotAtSequencingStage = true;
                                    break;
                                }
                            }
                        }

                        emit(
                            isThereAtLeastAnotherIndividual &&
                            isAtLeastOneIndividualExhausted &&
                            isSpeciesTopUpEqualsIndividualExhausted &&
                            !isSpecimenNotAtSequencingStage
                        );
                    """
                }
            }
        },
        'sample': {
            'calc_biospecimen_id': RuntimeFields.coalesce([
                'sts_sample_same_as',
                'sts_biospecimen_accession',
                'sts_sample_symbiont_of'
            ]),
            'calc_sts_export_eligible': {
                'type': 'boolean',
                'script': {
                    'source': """
                        String biospecimenId = null;
                        List biospecimenFields = [
                            'sts_sample_same_as.keyword',
                            'sts_biospecimen_accession.keyword',
                            'sts_sample_symbiont_of.keyword'
                        ];

                        for (String field : biospecimenFields) {
                            if (doc.containsKey(field) &&
                                doc[field].size() > 0) {
                                biospecimenId = doc[field].value;
                                break;
                            }
                        }

                        List requiredFields = [
                            'sts_tubeid.keyword',
                            'sts_species.sts_scientific_name.keyword',
                            'sts_species.id.keyword',
                            'sts_specimen.id.keyword',
                            'sts_organism_part.keyword',
                            'sts_lifestage.keyword',
                            'sts_preservation_approach.keyword',
                            'sts_sex.keyword',
                            'sts_tissue_size.keyword',
                            'sts_programme.keyword',
                            'sts_biosample_accession.keyword',
                            'sts_submit_date',
                            'sts_sampleset.id.keyword',
                            'sts_project.keyword',
                            'sts_species.sts_taxon_group.keyword',
                            'sts_species.sts_genome_size',
                            'sts_rackid.keyword',
                            'sts_pos_in_rack.keyword',
                            'sts_labwhere_parentage.keyword',
                            'sts_labwhere_name.keyword',
                            'sts_cost_code.keyword',
                            'sts_sequencescape_study_id.keyword'
                        ];

                        boolean basicFieldsExist = true;
                        for (String field : requiredFields) {
                            boolean fieldHasValue = false;

                            if (doc.containsKey(field)) {
                                if (field.endsWith(".keyword")) {
                                    fieldHasValue = doc[field].size() > 0;
                                } else {
                                    fieldHasValue = doc[field] != null;
                                }
                            }

                            if (!fieldHasValue) {
                                basicFieldsExist = false;
                                break;
                            }
                        }

                        boolean biospecimenIdExists = (biospecimenId != null);
                        emit(basicFieldsExist && biospecimenIdExists);
                    """
                }
            },
            'calc_benchling_remaining_weight': {
                'type': 'double',
                'script': {
                    'source': """
                        if (doc.containsKey('portaldb_date_abandoned') &&
                            doc['portaldb_date_abandoned'].size() > 0) {
                            emit(0.0);
                        } else if (doc.containsKey('benchling_remaining_weight') &&
                            doc['benchling_remaining_weight'].size() > 0) {
                            def value = doc['benchling_remaining_weight'].value;
                            if (!Double.isNaN(value)) {
                                emit(value);
                            } else {
                                emit(0.5);
                            }
                        } else {
                            emit(0.5);
                        }
                    """
                }
            },
            'calc_sample_abandoned_in_sts': {
                'type': 'boolean',
                'script': {
                    'source': """
                        boolean isSampleAbandoned = doc.containsKey('portaldb_date_abandoned') &&
                            doc['portaldb_date_abandoned'].size() > 0;

                        boolean isSampleInBenchling = doc.containsKey('sts_eln_id.keyword') &&
                            doc['sts_eln_id.keyword'].size() > 0;

                        if (isSampleAbandoned && !isSampleInBenchling) {
                            emit(true);
                        } else {
                            emit(false);
                        }
                    """
                }
            },
        },
        'sampleset': {
            'calc_tat_days': RuntimeFields.date_interval(
                'sts_submit_date',
                'sts_sample_sts_receive_date_min',
                'days'
            ),
            'calc_tat_weeks': RuntimeFields.date_interval(
                'sts_submit_date',
                'sts_sample_sts_receive_date_min',
                'weeks'
            )
        },
        'manifest': {
            'calc_tat_days': RuntimeFields.date_interval(
                'sts_submit_date',
                'sts_receive_date',
                'days'
            ),
            'calc_tat_weeks': RuntimeFields.date_interval(
                'sts_submit_date',
                'sts_receive_date',
                'weeks'
            )
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
            },
            'calc_mlwh_volume_remaining': {
                'type': 'double',
                'script': {
                    'source': """
                    if (doc.containsKey('portaldb_date_abandoned') &&
                        doc['portaldb_date_abandoned'].size() > 0) {
                        emit(0.0);
                    } else if (doc.containsKey('mlwh_volume_remaining') &&
                        doc['mlwh_volume_remaining'].size() > 0) {
                        def value = doc['mlwh_volume_remaining'].value;
                        if (!Double.isNaN(value)) {
                emit(value);
            } else {
                emit(0.5);
            }
        } else {
            emit(0.5);
        }
                """
                }
            },
        },
        'extraction': {
            'calc_dna_volume_remaining': RuntimeFields.coalesce([
                'mlwh_volume_si_value',
                'benchling_volume_ul',
            ], return_type='double'
            ),
            'calc_benchling_volume_ul': {
                'type': 'double',
                'script': {
                    'source': """
                    if (doc.containsKey('portaldb_date_abandoned') &&
                        doc['portaldb_date_abandoned'].size() > 0) {
                        emit(0.0);
                    } else if (doc.containsKey('benchling_volume_ul') &&
                        doc['benchling_volume_ul'].size() > 0) {
                        def value = doc['benchling_volume_ul'].value;
                        if (!Double.isNaN(value)) {
                emit(value);
            } else {
                emit(0.5);
            }
        } else {
            emit(0.5);
        }
                """
                }
            },
        },
        'tissue_prep': {
            'calc_benchling_weight_mg': {
                'type': 'double',
                'script': {
                    'source': """
                    if (doc.containsKey('portaldb_date_abandoned') &&
                        doc['portaldb_date_abandoned'].size() > 0) {
                        emit(0.0);
                    } else if (doc.containsKey('benchling_weight_mg') &&
                        doc['benchling_weight_mg'].size() > 0) {
                        def value = doc['benchling_weight_mg'].value;
                        if (!Double.isNaN(value)) {
                emit(value);
            } else {
                emit(0.5);
            }
        } else {
            emit(0.5);
        }
                """
                }
            }
        },
    }

    amd = data_source_attribute_metadata(
        portal_attributes()
    )

    # Set up the correct environment. Can be passed in as a parameter
    # or be ELASTIC_ENVIRONMENT environment variable
    # or not be set
    if environment is None:
        environment = os.getenv('ELASTIC_ENVIRONMENT', 'production')
    if product is None:
        product = os.getenv('ELASTIC_PRODUCT', 'portal')
    index_suffix = f'-{product}' if product else ''
    index_suffix += f'-{environment}' if environment else ''
    elastic = ElasticDataSource({
        'uri': os.getenv('ELASTIC_URI'),
        'user': os.getenv('ELASTIC_USER'),
        'password': os.getenv('ELASTIC_PASSWORD'),
        'index_prefix': os.getenv('ELASTIC_INDEX_PREFIX') + index_suffix,
        'relationship_cfg': relationship_config if product == 'portal' else {},
        'runtime_fields': runtime_fields if product == 'portal' else {}},
        attribute_metadata=amd)
    core_data_object(elastic)
    return elastic
