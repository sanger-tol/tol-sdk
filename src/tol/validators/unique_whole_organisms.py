# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import Validator
from tol.core.data_object import DataObject


class UniqueWholeOrganismsValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) not a SYMBIONT, it checks:
    1. There are no two samples with organism part WHOLE_ORGANISM with the same SPECIMEN_ID
    2. There are no samples with organism part *not* WHOLE_ORGANISM that have a SPECIMEN_ID
       the same as a WHOLE_ORGANISM in the manifest.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        symbiont_field: str
        organism_part_field: str
        specimen_id_field: str

    __slots__ = ['__config', '__whole_organisms', '__part_organisms']
    __config: Config
    __whole_organisms: List[str]
    __part_organisms: List[str]

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__whole_organisms = []
        self.__part_organisms = []
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function uses a bit of a confusing method for its validation, so I'm going to
        # leave an explanation here as to how it works for anyone who needs to modify it
        # in the future!
        #
        # In the original code to be adapted, two loops were used. The first looped over each
        # data object whose ORGANISM_PART was 'WHOLE_ORGANISM', adding them to a list. Before it
        # did this though, it would check to see if the SPECIMEN_ID of this data object was already
        # contained in said list (to ensure the specimen IDs were unique). In the second loop, the
        # rest of the data objects (those whose ORGANISM PART was *not* 'WHOLE_ORGANISM') were
        # looped over, each being checked to see if their SPECIMEN_ID was contained in the list
        # (the one containing the whole organisms). In all, this ensures that all whole organisms
        # have unique specimen IDs, and all part organisms do not share the specimen IDs of any of
        # the whole organisms.
        #
        # The issue when adapting this to a Validator to be used in a pipeline, is that this
        # function only takes in one data object at a time, via a generator (to save needing to
        # load many into memory at once). The problem this left us with is that we could no longer
        # achieve the same result by using two passes of the data, as only one pass was feasible.
        #
        # So here's what I ended up with. This validator stores the SPECIMEN_IDs of both all of the
        # whole organisms *and* part organisms. From this, detecting duplicate whole organisms is
        # the same, but detecting whether a part organism shared the SPECIMEN_ID of a whole
        # organism now has two separate cases: when the data object passed into this function is
        # a whole organism, or a part organism. In the case of it being a part organism, a very
        # similar solution to before can be used: we simply check whether self.__whole_organisms
        # conatins the same SPECIMEN_ID. However, for the case where the data object is a whole
        # organism, effectively the inverse is done; it is the self.__part_organisms list that is
        # checked. This covers all cases:
        #   1. There are no duplicates, in which case there will never be a time when the same
        #      SPECIMEN_ID will be in both lists.
        #   2. A whole organism is checked, then a part organism with the same SPECIMEN_ID is
        #      checked. In this case, self.__whole_organisms will contain the same SPECIMEN_ID,
        #      so the duplicate is detected.
        #   3. A part organism is checked, then a whole organism with the same SPECIMEN_ID is
        #      checked. In this case, self.__part_organisms will contain the same SPECIMEN_ID,
        #      so the duplicate is detected.
        #
        # From Thomas :)

        # Ensure the data object is not a SYMBIONT, because organism part checks do not apply
        if obj.attributes.get(self.__config.symbiont_field) != 'SYMBIONT':
            specimen_id = obj.attributes.get(self.__config.specimen_id_field)
            if specimen_id is None:
                return

            organism_part = obj.attributes.get(self.__config.organism_part_field)
            if organism_part == 'WHOLE_ORGANISM':
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='No two whole organisms can have the same Specimen ID',
                        field=self.__config.specimen_id_field,
                    )
                if specimen_id in self.__part_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='A whole organism cannot have a Specimen ID already used for'
                               'a non-whole organism',
                        field=self.__config.specimen_id_field,
                    )

                self.__whole_organisms.append(specimen_id)
            else:
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='A non-whole organism cannot have a Specimen ID already used for'
                               'a whole organism',
                        field=self.__config.specimen_id_field,
                    )

                self.__part_organisms.append(specimen_id)
