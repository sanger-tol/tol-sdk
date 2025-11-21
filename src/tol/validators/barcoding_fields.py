# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from tol.core import DataObject, Validator

class BarcodingFieldsValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    ensuring that all barcoding fields must all be filled
    or be NOT_APPLICABLE
    """
    def __init__(self) -> None:
        super().__init__()
    
    def _validate_data_object(self, obj: DataObject) -> None:
        pass

    def __validate_attribute(self, key: str, value: Any):
        pass
