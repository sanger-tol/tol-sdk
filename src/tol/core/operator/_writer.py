# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from functools import cache

from .enum import RelationWriteMode


class _Writer:
    """
    A (private-API) class that documents
    how to perform writes for related
    instances of `DataObject`.
    """

    @property
    @cache
    def write_mode(
        self
    ) -> dict[str, RelationWriteMode]:
        """
        The `WriteMode` value for this
        `object_type` on this `DataSource`
        instance.

        Override for custom behaviour.
        """

        return {
            type_: self._default_write_mode
            for type_ in self.supported_types
        }

    @property
    def _default_write_mode(
        self
    ) -> RelationWriteMode:
        """
        Return a value on child instances if
        the value of `WriteMode` is the same for
        every key in `supported_types`.
        """

        return RelationWriteMode.NOT_APPLICABLE

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        pass
