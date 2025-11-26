# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, cast

from tol.core import Validator
from tol.core.data_object import DataObject


Config = Dict[str, str]


class UniqueWholeOrganismsValidator(Validator):
    __slots__ = ('__whole_organisms', '__config')
    __whole_organisms: List[str]
    __config: Config

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.__whole_organisms = []
        self.__config = config
    
    def _validate_data_object(self, obj: DataObject) -> None:
        if obj.get_field_by_name(self.__config['symbiont_field']) != 'SYMBIONT':
            specimen_id = cast(str, obj.get_field_by_name(self.__config['specimen_id_field']))

            if obj.get_field_by_name(self.__config['organism_part_field']) == 'WHOLE_ORGANISM':
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='WHOLE_ORGANISM can only be used once',
                        field=self.__config['specimen_id_field'],
                    )
                
                self.__whole_organisms.append(specimen_id)
            else:
                if specimen_id in self.__whole_organisms:
                    self.add_error(
                        object_id=obj.id,
                        detail='Cannot reuse a spcimen ID that as been used for WHOLE_ORGANISM',
                        field='SPECIMEN_ID'
                    )

