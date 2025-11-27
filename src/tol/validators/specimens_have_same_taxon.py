# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict

from tol.core import Validator
from tol.core.data_object import DataObject


Config = Dict[str, str]


class SpecimensHaveSameTaxonValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) not a SYMBIONT, it checks:
    1. There are no samples with SPECIMEN_ID which has different TAXON_ID
    """
    __slots__ = ['__config', '__seen']
    __config: Config
    __seen: Dict[str, str]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.__seen = {}
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # Explaining the code concept using a standard example
        # seen{}
        # 1st Pass=>    element['specimen_id']  =   A
        #               element['taxon_id']     =   AA
        #               seen{ A:AA }
        # 2nd pass=>    element['specimen_id']  =   A
        #               element['taxon_id']     =   AB
        #               AB != AA
        #               Flag error 
        # From Nithin :)

        # Ensure the data object is not a SYMBIONT
        if obj.attributes.get(self.__config_value('symbiont_field')) != 'SYMBIONT':
            specimen_id = obj.attributes.get(self.__config_value('specimen_id_field'))
            if specimen_id is None:
                return
            taxon_id = obj.attributes.get(self.__config_value('taxon_id_field'))
            if taxon_id is None:
                return
            if specimen_id in self.__seen and taxon_id != self.__seen[specimen_id]:
                    self.add_error(
                        object_id=obj.id,
                        detail='A specimen must have the same taxonomy ID',
                        field=self.__config_value('specimen_id_field'),
                    )
            if specimen_id not in self.__seen:
                self.__seen[specimen_id] = taxon_id

    def __config_value(self, key: str) -> Any:
        """
        A reusable function that handles extracting a key from the config, handling the case
        that it is not present.
        """
        try:
            return self.__config[key]
        except KeyError:
            raise Exception(f'VALIDATOR SETUP ERROR: '
                            f'{key} not present in the config for SpecimensHaveSameTaxonValidator')