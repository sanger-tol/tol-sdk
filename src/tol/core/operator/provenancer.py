# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class ProvenanceField:
    source_order: list[str]
    return_type: str


ProvenanceFields = dict[str, ProvenanceField]


class Provenancer(ABC):
    pass
