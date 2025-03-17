# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GenomeNotesGenomeNoteToElasticGenomeNoteConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:

        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['taxid', 'tolid', 'assembly_accession']
        }
        to_one_relations = {
            'assembly': self._data_object_factory(
                'assembly',
                data_object.assembly_accession),
            'tolid': self._data_object_factory(
                'tolid',
                data_object.tolid
            ),
            'species': self._data_object_factory(
                'species',
                str(data_object.taxid)
            )
        }
        ret = self._data_object_factory(
            'genome_note',
            data_object.id,
            attributes=attributes,
            to_one=to_one_relations
        )
        yield ret
