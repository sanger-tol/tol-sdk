# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
)


class GenomeNoteConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = dict(data_object.attributes)
        output_attributes = {}

        rename = dict(self.rename_attributes())

        metadata = attributes.get('metadata', {})
        methods = attributes.get('methods', {})
        assembly_stats = attributes.get('assembly_stats', {})

        for key in (
            'data_availability',
            'title',
            'abstract',
            'keywords',
            'background',
            'bioproject',
        ):
            output_attributes[key] = metadata.get(key, '')

        output_attributes['authors'] = [
            author.get('given_names', '') + ' ' + author.get('surname', '')
            for author in metadata.get('authors', [])
        ]

        if 'references' in attributes:
            output_attributes['references'] = attributes['references']

        for key, value in methods.items():
            output_attributes[rename.get(key, key)] = value

        for key, value in assembly_stats.get('sequence_report', {}).items():
            output_attributes[key] = value

        output_attributes['assembly_stats_analysis'] = assembly_stats.get(
            'analysis',
            {},
        )

        output_attributes['assembly_stats_assembly_graphs'] = assembly_stats.get(
            'assembly_graphs',
            {},
        )

        for key in (
            'chromosomal_pseudomolecules',
            'samples',
            'other',
        ):
            output_attributes[key] = assembly_stats.get(
                key,
                [] if key != 'other' else {},
            )

        species_list = assembly_stats.get('species', [])
        for species_obj in species_list:
            for k, v in species_obj.items():
                output_attributes[f'species_{k}'] = v
            break

        for key in self.as_is_attributes():
            if key in attributes:
                output_attributes[key] = attributes[key]

        yield self._data_object_factory(
            type_='genome_note',
            id_=metadata.get('doi', None),
            attributes=output_attributes
        )

    def rename_attributes(self):
        return (
            ('sample_acquisition', 'method_sample_acquisition'),
            ('nucleic_acid_extraction', 'method_nucleic_acid_extraction'),
            (
                'pacbio_library_prep_and_sequencing',
                'method_pacbio_library_prep_and_sequencing',
            ),
            (
                'hic_sample_prep_and_crosslinking',
                'method_hic_sample_prep_and_crosslinking',
            ),
            (
                'hic_library_prep_and_sequencing',
                'method_hic_library_prep_and_sequencing',
            ),
        )

    def as_is_attributes(self):
        return (
            'software_tools',
        )
