# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GenomeNotesGenomeNoteToElasticGenomeNoteConverter(
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

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:

        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['taxid', 'tolid', 'assembly_accession', 'authors']
        }
        if data_object.authors:
            attributes['authors'] = [
                author.strip() for author in data_object.authors.split(',')
            ]
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
