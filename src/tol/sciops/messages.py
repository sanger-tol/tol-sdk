# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass
class Sample:
    sample_uuid: str
    study_uuid: str = None
    sanger_sample_id: str = None
    location: str = None
    supplier_sample_name: str = None
    volume: str = None
    concentration: str = None
    public_name: str = None
    taxon_id: str = None
    common_name: str = None
    donor_id: str = None
    library_type: str = None
    country_of_origin: str = None
    sample_collection_date_utc: datetime = None


@dataclass
class Update:
    uuid: str
    name: str
    value: str


@dataclass
class LabwareMessage:
    SUBJECT = None
    VERSION = "latest"
    message_uuid: str
    message_create_date_utc: datetime = None


@dataclass
class CreateLabwareMessage(LabwareMessage):
    SUBJECT = "create-labware"
    labware_type: str = None
    labware_uuid: str = None
    barcode: str = None
    samples: List[Sample] = field(default_factory=list)


@dataclass
class UpdateLabwareMessage(LabwareMessage):
    SUBJECT = "update-labware"
    labware_updates: List[Update] = field(default_factory=list)
    sample_updates: List[Update] = field(default_factory=list)
