# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC


class Archetype(ABC):
    """
    Specifies behaviour for a declarative Archetype
    class for an object_type. Contains:

    - fields
    - relationships
    - metadata
    """
