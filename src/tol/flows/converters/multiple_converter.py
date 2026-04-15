# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter
from tol.core.operator.updater import DataObjectUpdate


class MultipleConverter(DataObjectToDataObjectOrUpdateConverter):
    """
    Convert DataObjects using multiple converters in a chain.
    The output of each converter is fed as input to the next one.

    {
        "converters": [{
            "module": "<path.to.module>",
            "class_name": "<path.to.ConverterClass>",
            "config_details": { ... }
        }]
    }

    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        converters: list[dict]

    __slots__ = [
        '__converters'
    ]

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__converters = []

        for conv in config.converters:
            __module = importlib.import_module(conv.get('module'))
            converter_class = getattr(__module, conv.get('class_name'))

            converter_conf = converter_class.Config(
                **conv.get('config_details')
            )
            self.__converters.append(converter_class(
                data_object_factory=data_object_factory,
                config=converter_conf,
            ))

    def convert_iterable(
        self,
        inputs: Iterable[DataObject | DataObjectUpdate]
    ) -> Iterable[DataObject]:
        converted_objs = inputs
        for converter in self.__converters:
            converted_objs = converter.convert_iterable(converted_objs)
        yield from converted_objs

    def convert(self, data_object: DataObject) -> Iterable[DataObject | DataObjectUpdate]:
        yield from self.convert_iterable([data_object])
