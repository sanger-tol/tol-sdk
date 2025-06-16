# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections import ChainMap
from collections.abc import Mapping
from functools import cached_property

from pydantic import BaseModel, Field, computed_field


class FileConfig(BaseModel):
    format_: str = Field(alias='format')
    header: bool
    name: str
    submitter: str

    comment: str = '#'
    default_reference_header: str | None = Field(
        None,
        alias='default reference header',
    )


class DestinationConfig(BaseModel):
    key: str

    imported_values: list[str | dict[str, str]] = []
    separator: str = '|'
    ignore: list[str] = []

    @computed_field(return_type=list[type])
    @cached_property
    def magic_types(self) -> list[type]:
        type_map = {
            'int': int,
            'double': float,
        }

        return [
            v
            for k, v in type_map.items()
            if k in self.imported_values
        ]

    @computed_field(return_type=bool)
    @property
    def magic_match_all(self) -> bool:
        return 'all' in self.imported_values

    @computed_field(return_type=dict[str, str])
    @cached_property
    def imported_values_map(self) -> dict[str, str]:
        maps = [
            a
            for a
            in self.imported_values
            if isinstance(a, Mapping)
        ]
        chained_map = dict(
            ChainMap(*maps)
        )
        literal_dict = {
            a: a
            for a in self.imported_values
            if not isinstance(a, Mapping)
        }

        return chained_map | literal_dict


class AttributeConfig(BaseModel):
    imported_column_name: str
    column_reference: str
    destination: DestinationConfig | list[DestinationConfig]


class YamlConfig(BaseModel):
    file: FileConfig
    attributes: list[AttributeConfig] = Field(
        min_length=1,
    )
