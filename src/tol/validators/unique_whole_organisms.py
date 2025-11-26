# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import List, cast

from tol.core import Validator
from tol.core.data_object import DataObject


class UniqueWholeOrganismsValidator(Validator):
    __slots__ = ('__whole_organisms')
    __whole_organisms: List[str]

    def __init__(self) -> None:
        super().__init__()
        self.__whole_organisms = []
    
    def _validate_data_object(self, obj: DataObject) -> None:
        if obj.attributes.get('SYMBIONT') != 'SYMBIONT':
            specimen_id = cast(str, obj.attributes.get('SPECIMEN_ID'))

            if obj.attributes.get('ORGANISM_PART') == 'WHOLE_ORGANISM':
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='WHOLE_ORGANISM can only be used once',
                        field='SPECIMEN_ID',
                    )
                
                self.__whole_organisms.append(specimen_id)
            else:
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='Cannot reuse a spcimen ID that as been used for WHOLE_ORGANISM',
                        field='SPECIMEN_ID'
                    )

