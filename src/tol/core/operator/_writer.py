# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from functools import cache

from .enum import (
    RelationWriteMode,
    ReturnMode
)


class _Writer:
    """
    A (private-API) class that documents:

    - how to perform writes for related
      instances of `DataObject`.
    - what types write methods return
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
    @cache
    def return_mode(
        self
    ) -> dict[str, ReturnMode]:
        """
        The `ReturnMode` value for this
        `object_type` on this `DataSource`
        instance.

        Override for custom behaviour.
        """

        return {
            type_: self._default_return_mode
            for type_ in self.supported_types
        }

    @property
    def _default_write_mode(
        self
    ) -> RelationWriteMode:
        """
        Unless `write_mode` is overriden, this
        is the value for all `supported_types`.
        """

        return RelationWriteMode.NOT_APPLICABLE

    @property
    def _default_return_mode(
        self
    ) -> ReturnMode:
        """
        Unless `return_mode` is overriden, this
        is the value for all `supported_types`.
        """

        return ReturnMode.NONE

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        pass
