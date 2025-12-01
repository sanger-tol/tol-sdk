# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List

from tol.core import Validator
from tol.core.data_object import DataObject
from tol.ena.ena_datasource import DataSource 

Config = Dict[str, str]

class UniqueWholeOrganismsValidator(Validator):
    """
    validates the ENA_CHECKLIST for each samples 
    """
    __slots__ = ['__config']
    
    def __init__(self, config: Config) -> None:
        super().__init__()
    
    def _validate_data_object(self, obj: DataObject) -> None:
        ena_checklist = DataSource.get_list("checklist")
        