# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToStsSampleConverter(
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
        eln_updated_at = data_object.sts_eln_updated_at
        if not eln_updated_at \
                and data_object.benchling_eln_tissue_id is not None:
            eln_updated_at = datetime.now()
        yield self._data_object_factory(
            'sample',
            data_object.id,
            attributes={
                'public_name':
                    data_object.tolid.id
                    if data_object.tolid else None,
                'eln_id': data_object.benchling_eln_tissue_id,
                'ep_exported': True if data_object.benchling_eln_tissue_id else False,
                'eln_updated_at': eln_updated_at,
            }
        )
