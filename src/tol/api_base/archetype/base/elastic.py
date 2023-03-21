# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC

from .base import Archetype
from ...utils.config import IndividualConfig
from ....elastic import ElasticDataSource


class ElasticArchetype(Archetype, ABC):
    """
    The ABC Archetype for objects stored in
    ElasticSearch.
    """

    # note - to achieve "Separation of Concerns",
    # ElasticDataSource is intitialised elsewhere, and
    # given to the constructor for every object_type

    def to_config(self) -> IndividualConfig:
        return super().to_config()
