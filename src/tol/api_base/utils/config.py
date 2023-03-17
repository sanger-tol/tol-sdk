# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tol.api_base import IdSchemes, tol_fields


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
    object type, as expressed in terms of methods acting
    on objects and data sources.
    """

    object_type: ObjectType
    id_scheme: IdSchemes
    methods: MethodsDict
    meta: Optional[MetaDict] = None
    attributes: Optional[AttributesDict] = None
    relationships: Optional[ConfigRelationships] = None

    def __post_init__(self):
        if self.relationships is not None:
            self.relationships = ConfigRelationships(
                **self.relationships
            )


Config = Dict[str, IndividualConfig]
