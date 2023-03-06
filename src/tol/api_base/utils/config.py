# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, List

from tol.api_base import IdSchemes, Methods, Sources, tol_fields


@dataclass
class OneRelationshipConfig:
    key: str
    target_type: str
    field: tol_fields.ForeignKey


@dataclass
class ConfigRelationships:
    one: Dict[str, OneRelationshipConfig]
    many: List[str]

    def __post_init__(self):
        self.one = {
            key: OneRelationshipConfig(
                **value
            )
            for key, value in self.one.items()
        }


@dataclass
class IndividualConfig:
    type_: str
    id_scheme: IdSchemes
    meta: Dict[str, Any]
    source: Sources
    methods: Dict[str, List[Methods]]
    attributes: Dict[str, tol_fields.Field]
    relationships: ConfigRelationships

    def __post_init__(self):
        self.relationships = ConfigRelationships(
            **self.relationships
        )


Config = Dict[str, IndividualConfig]
