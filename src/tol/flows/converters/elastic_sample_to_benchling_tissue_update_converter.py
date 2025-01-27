# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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

    def _convert_one(self, data_object: DataObject) -> DataObjectUpdate:
        if data_object is None:
            return
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
                        species.sts_taxon_group
                        if species.sts_taxon_group else 'NA',
                    'genome_size': str(species.sts_genome_size),
                    # 'freezer': None,
                    'location': data_object.sts_labwhere_parentage,  # Previously shelf
                    'tray': data_object.sts_labwhere_name,
                    'specimen_id': specimen.id,
                    'programme_id': data_object.sts_tolid.id,
                    'biosample_id': data_object.sts_biosample_accession,
                    'biospecimen_id': data_object.calc_biospecimen_id,  # Needs work
                    'organism_part':
                        ', '.join(data_object.sts_organism_part)
                        if data_object.sts_organism_part is not None else None,
                    'lifestage': data_object.sts_lifestage,
                    'sex': data_object.sts_sex,
                    'preservation_approach': data_object.sts_preservation_approach,
                    'size_of_tissue_in_tube': data_object.sts_tissue_size,
                    'date_sample_received_at_sanger':
                        data_object.sts_receive_date.strftime('%Y-%m-%d')
                        if data_object.sts_receive_date is not None else '1970-01-01',
                    'date_assigned_to_lab':
                        data_object.sts_tollab_assign_date.strftime('%Y-%m-%d')
                        if data_object.sts_tollab_assign_date is not None else '1970-01-01',
                    # 'assigned_by': ,
                    # 'lab_work_category': data_object.sts_lab_work_category,
                    'family_representative': ', '.join(species.goat_family_representative)
                        if species.goat_family_representative is not None else None,
                    'sample_set_id': data_object.sts_sampleset.id,
                    'rd_sample': data_object.sts_send_rd,
                    'sts_id': int(data_object.id),
                    # 'remaining_weight':,
                    'priority': data_object.sts_priority,
                    'project': ', '.join(data_object.sts_project),
                    'study_id': data_object.sts_sequencescape_study_id,
                    'cost_code': data_object.sts_cost_code,
                }
            )
            return ret

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object.benchling_eln_tissue_id is not None:
            ret = self._convert_one(data_object)
            if ret is not None:
                yield ret
