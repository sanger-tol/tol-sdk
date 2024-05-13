# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticSampleToBenchlingTissueUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object.benchling_eln_tissue_id is not None:
            species = data_object.to_one_relationships['sts_species']
            specimen = data_object.to_one_relationships['sts_specimen']
            if species is not None and specimen is not None:
                ret = (
                    data_object.benchling_eln_tissue_id,
                    {
                        'rack_id': data_object.sts_rackid,
                        'tube_well_id': data_object.sts_tubeid,
                        'tube_position': data_object.sts_pos_in_rack,
                        'scientific_name': species.sts_scientific_name,
                        'taxon_id': species.id,
                        'taxon_group_phyla':
                            species.sts_order_group
                            if species.sts_order_group != '' else 'NA',
                        'genome_size': str(species.sts_genome_size),
                        'freezer': None,
                        'shelf': data_object.sts_labwhere_parentage,
                        'tray': data_object.sts_labwhere_name,
                        'specimen_id': specimen.id,
                        'programme_id': data_object.sts_tolid.id,
                        'biosample_id': data_object.sts_biosample_accession,
                        # 'biospecimen_id': sample.sts_biospecimen_accession,  # Needs work
                        # 'organism_part': sample.sts_organism_part,
                        # 'lifestage': sample.sts_lifestage,
                        # 'sex': sample.sts_sex,
                        # 'preservation_approach': sample.sts_preservation_approach,
                        # 'size_of_tissue_in_tube': sample.sts_tissue_size,
                        'date_sample_received_at_sanger':
                            data_object.sts_receive_date.strftime('%Y-%m-%d'),
                        'date_assigned_to_lab':
                            data_object.sts_tollab_assign_date.strftime('%Y-%m-%d'),
                        # 'assigned_by': ,
                        # 'lab_work_category': ,
                        # 'family_representative': ,
                        'sample_set_id': data_object.sts_sampleset_id,
                        'rd_sample': data_object.sts_send_rd,
                        'sts_id': int(data_object.id),
                        # 'remaining_weight':,
                        'priority': data_object.sts_priority,
                        'project': ', '.join(data_object.sts_project),
                    }
                )
                yield ret
