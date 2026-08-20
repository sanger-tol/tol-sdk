# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticSampleToBenchlingTissueUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def _convert_one(self, data_object: DataObject) -> DataObjectUpdate:
        if data_object is None:
            return
        species = data_object.to_one_relationships['species']
        specimen = data_object.to_one_relationships['specimen']

        if species is not None and specimen is not None:
            ret = (
                data_object.eln_tissue_id or data_object.eln_id,
                {
                    'rack_id': data_object.rackid,
                    'tube_well_id': data_object.tubeid,
                    'tube_position': data_object.pos_in_rack,
                    'scientific_name': species.scientific_name,
                    'taxon_id': species.id,
                    'taxon_group_phyla':
                        species.taxon_group
                        if species.taxon_group else 'NA',
                    'genome_size': str(species.genome_size),
                    # 'freezer': None,
                    'location': data_object.location_parentage,
                    'tray': data_object.location_name,
                    'specimen_id': specimen.id,
                    'programme_id': data_object.tolid.id,
                    'biosample_id': data_object.biosample_accession,
                    'biospecimen_id': data_object.calc_biospecimen_id,  # Needs work
                    'organism_part':
                        ', '.join(data_object.organism_part)
                        if data_object.organism_part is not None else None,
                    'lifestage': data_object.lifestage,
                    'sex': data_object.sex,
                    'preservation_approach': data_object.preservation_approach,
                    'size_of_tissue_in_tube': data_object.tissue_size,
                    'hazard_group': data_object.hazard_group,
                    'date_sample_received_at_sanger':
                        data_object.receive_date.strftime('%Y-%m-%d')
                        if data_object.receive_date is not None else '1970-01-01',
                    'date_assigned_to_lab':
                        data_object.tollab_assign_date.strftime('%Y-%m-%d')
                        if data_object.tollab_assign_date is not None else '1970-01-01',
                    # 'assigned_by': ,
                    # 'lab_work_category': data_object.sts_lab_work_category,
                    'family_representative': ', '.join(species.family_representative)
                        if species.family_representative is not None else None,
                    'sample_set_id': data_object.sampleset.id,
                    'rd_sample': data_object.send_rd,
                    'sts_id': int(data_object.id),
                    # 'remaining_weight':,
                    'priority': data_object.priority,
                    'project': data_object.project,
                    'study_id': data_object.sequencescape_study_id,
                    'cost_code': data_object.cost_code,
                }
            )
            return ret

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object.eln_tissue_id is not None or data_object.eln_id is not None:
            ret = self._convert_one(data_object)
            if ret is not None:
                yield ret
