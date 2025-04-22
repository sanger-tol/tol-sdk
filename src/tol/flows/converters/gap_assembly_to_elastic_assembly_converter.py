# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GapAssemblyToElasticAssemblyConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert_details(self, assembly: DataObject) -> Iterable[DataObject]:
        return {
            d.id.replace(' ', '_').lower(): d.info
            for d in assembly.assembly_details
        }

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        details = self.convert_details(data_object)

        to_one_relations = {
            'species': self._data_object_factory(
                'species',
                str(data_object.taxon_id)
            ),
        }

        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['taxon_id', 'species', 'phylum_id', 'phylum']
        }

        detail_attributes = {
            k: v
            for k, v in details.items()
            if k in ['organelles', 'total_ingapped_length', 'total_sequence_length',
                     'number_of_chromosomes', 'scaffold_n50', 'number_of_scaffolds',
                     'contig_n50', 'number_of_contigs', 'gc_percent', 'genome_coverage']
        }

        ret = self._data_object_factory(
            'assembly',
            data_object.id,
            attributes={
                **detail_attributes,
                **attributes
            },
            to_one=to_one_relations
        )
        yield ret
