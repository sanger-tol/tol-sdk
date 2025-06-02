# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core.validate import Validator


class AllowedKeysValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    ensuring that they only have attributes of the given
    allowed keys.
    """

    def __init__(
        self,
        allowed_keys: list[str],
        *,
        is_error: bool = True,
    ) -> None:

        super().__init__()

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> DataObject:

        pass
