# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
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
        extra_attributes: dict = field(default_factory=dict)
        only_if_new: bool = False

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config):
        super().__init__(data_object_factory)
        self.__config = config
        self.update_converter = ElasticSampleToBenchlingTissueUpdateConverter(
            data_object_factory=self._data_object_factory,
            config=config
        )

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if self.__config.only_if_new and data_object.sts_eln_id is not None:
            return
        converted_update = self.update_converter._convert_one(data_object)
        if converted_update is not None:
            id_, attributes = converted_update
            ret = self._data_object_factory(
                'tissue',
                id_,
                attributes=attributes | self.__config.extra_attributes
            )
            yield ret
        else:
            yield None
