# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class AutoDetectManifestTypeConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        rack_or_plate: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        converting the samples DataObject into ENA format
        """
        s = data_object
        attributes = {}
        rack_or_plate_based_manifest = bool(
            re.fullmatch(r'^[A-P][12]?[0-9]$',
                         s.attributes.get(self.__config.rack_or_plate))
        )

        if rack_or_plate_based_manifest:
            attributes['manifest_type'] = 'PLATE_WELL'
        else:
            attributes['manifest_type'] = 'RACK_TUBE'

        ret = self._data_object_factory(
            data_object.type,
            s.id,
            attributes=attributes,
        )
        yield ret
