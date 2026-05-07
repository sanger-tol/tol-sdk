# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import (
    Iterable
)

from .elastic_sample_to_benchling_tissue_update_converter import (
    ElasticSampleToBenchlingTissueUpdateConverter
)
from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToBenchlingTissueConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config):
        super().__init__(data_object_factory)
        self.update_converter = ElasticSampleToBenchlingTissueUpdateConverter(
            data_object_factory=self._data_object_factory,
            config=config
        )

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        converted_update = self.update_converter._convert_one(data_object)
        if converted_update is not None:
            id_, attributes = converted_update
            ret = self._data_object_factory(
                'tissue',
                id_,
                attributes=attributes
            )
            yield ret
        else:
            yield None
