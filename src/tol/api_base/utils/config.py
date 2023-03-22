# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils import tol_fields
from ...core.datasource import DataSource


ObjectType = str
Method = str
MetaDict = Dict[str, Any]
MethodsDict = Dict[str, List[Method]]
AttributesDict = Dict[str, tol_fields.Field]


OneRelationshipDict = Dict[str, tol_fields.ToOneRelationship]
ManyRelationshipDict = Dict[str, ObjectType]


@dataclass
class ConfigRelationships:
    one: Optional[OneRelationshipDict] = None
    many: Optional[ManyRelationshipDict] = None


@dataclass
class IndividualConfig:
    """
    Configures the core (non-custom) behaviour of an
    object_type, as expressed in terms of methods acting
    on objects of its own type and DataSource, as well as
    others.
    """

    object_type: ObjectType
    data_source: DataSource
    id_field: tol_fields.Id
    methods: MethodsDict
    meta: Optional[MetaDict] = None
    attributes: Optional[AttributesDict] = None
    relationships: Optional[ConfigRelationships] = None

    def __post_init__(self):
        if self.relationships is not None:
            self.relationships = ConfigRelationships(
                **self.relationships
            )


CombinedConfig = Dict[str, IndividualConfig]
