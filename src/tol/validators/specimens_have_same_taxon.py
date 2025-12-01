# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

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
        if obj.attributes.get(self.get_config(self.__config,
                                              'symbiont_field',
                                              'SpecimensHaveSameTaxonValidator')) != 'SYMBIONT':
            specimen_id = obj.attributes.get(self.get_config(self.__config,
                                                             'specimen_id_field',
                                                             'SpecimensHaveSameTaxonValidator'))
            if specimen_id is None:
                return
            taxon_id = obj.attributes.get(self.get_config(self.__config,
                                                          'taxon_id_field',
                                                          'SpecimensHaveSameTaxonValidator'))
            if taxon_id is None:
                return
            if specimen_id in self.__seen and taxon_id != self.__seen[specimen_id]:
                self.add_error(
                    object_id=obj.id,
                    detail='A specimen must have the same taxonomy ID',
                    field=self.get_config(self.__config,
                                          'specimen_id_field',
                                          'SpecimensHaveSameTaxonValidator'),
                )
            if specimen_id not in self.__seen:
                self.__seen[specimen_id] = taxon_id
