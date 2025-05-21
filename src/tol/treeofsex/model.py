# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pydantic import BaseModel, Field


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
    imported_values: list[str | dict[str, str]] = Field(
        min_length=1,
    )

    separator: str = '|'
    ignore: list[str] = []


class AttributeConfig(BaseModel):
    imported_column_name: str
    column_reference: str
    destination: DestinationConfig


class YamlConfig(BaseModel):
    file: FileConfig
    attributes: list[AttributeConfig] = Field(
        min_length=1,
    )
