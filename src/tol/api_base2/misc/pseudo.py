# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

from ...core import DataObject


class PseudoObjectError(NotImplementedError):
    def __init__(self, obj: object) -> None:
        super().__init__(
            f'The pseudo object class {type(obj).__name__} '
            'has limited functionality - this is not supported.'
        )


class PseudoObject(DataObject):
    """
    Supports just enough of `DataObject` to be useful to
    `Upserter().upsert()`.
    """

    def __init__(
        self,
        type_: str,
        id_: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
        to_ones: Optional[dict[str, DataObject]] = None
    ) -> None:

        self.__type = type_
        self.__id = id_
        self.__attributes = attributes
        self.__to_ones = to_ones

    @property
    def attributes(self) -> dict[str, Any]:
        return self.__attributes

    @property
    def id(self) -> Optional[str]:  # noqa A007
        return self.__id

    @property
    def type(self) -> str:  # noqa A007
        return self.__type

    @property
    def to_one_relationships(self) -> None:
        return PseudoObjectError(self)

    @property
    def to_many_relationships(self) -> None:
        raise PseudoObjectError(self)

    @property
    def _host(self) -> None:
        raise PseudoObjectError(self)

    @property
    def _to_one_objects(self) -> None:
        return self.__to_ones
