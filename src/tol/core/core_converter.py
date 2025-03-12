# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from functools import reduce
from itertools import chain
from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    Optional,
    TypeVar
)

if typing.TYPE_CHECKING:
    from .data_loader import DataLoader


In = TypeVar('In')
"""The input representation type"""


Out = TypeVar('Out')
"""The output representation type"""


class Converter(ABC, Generic[In, Out]):
    """
    A useful `ABC` for converting from one representation to another.
    """

    def convert_iterable(
        self,
        inputs: Iterable[Optional[In]]
    ) -> Iterable[Optional[Out]]:
        """
        Converts an `Iterable` of (possibly `None`) input representations
        to an `Iterable` of (possibly `None`) output representations,
        according to the rules of `convert_optional()`
        """

        return (self.convert_optional(i) for i in inputs)

    def convert_optional(self, input_: Optional[In]) -> Optional[Out]:
        """
        Converts a possibly `None` input representation to either:

        - `None` if the input is `None`
        - `convert(input)` if the input is not `None`
        """

        return self.convert(input_) if input_ is not None else None

    @abstractmethod
    def convert(self, input_: In) -> Out:
        """
        Converts an input representation to an output representation.

        If the input could be `None`, use `convert_optional()` instead.
        """


class AsyncConverter(ABC, Generic[In, Out]):
    """An asynchronous version of `Converter`"""

    @abstractmethod
    async def async_convert(self, input_: In) -> Out:
        """input_ must not be null."""

    async def async_convert_optional(self, input_: Optional[In]) -> Optional[Out]:
        """input_ can be `None`, in which case `None` is returned"""

        return await self.async_convert(input_) if input_ is not None else None

    async def async_convert_iterable(
        self,
        input_: Iterable[Optional[In]]
    ) -> Iterable[Optional[Out]]:
        """
        Converts an `Iterable`, converting or returning `None` element-wise,
        using `AsyncConverter().async_convert_optional()`
        """

        return [
            await self.async_convert_optional(i) for i in input_
        ]


def is_iter(in_: Any) -> bool:
    try:
        iter(in_)
        return True
    except TypeError:
        return False


class ChainedConverter(Converter, Generic[In, Out]):
    """
    Using multiple converters in sequence, converts in a chain.

    e.g. with `Converter` instances, `a` and `b`, this is roughly
    equivalent to:

    ```
    def convert(self, input_: In) -> Out:
        inner = a.convert(input_)
        return b.convert(inner)
    ```

    Please note that this is different to the main `Converter` -
    `None` elements are ignored in the sequence. Only use the
    `convert_iterable` method.
    """

    def __init__(
        self,
        *converters: Converter
    ):
        self.__converters = converters
        self.__data_loader = None

    @property
    def data_loader(self) -> DataLoader | None:
        return self.__data_loader

    @data_loader.setter
    def data_loader(self, dl: DataLoader) -> None:
        self.__data_loader = dl
        for converter in self.__converters:
            converter.data_loader = dl

    def convert_iterable(
        self,
        inputs: Iterable[In | None]
    ) -> Iterator[Out]:

        return chain.from_iterable(
            self.convert_optional(input_)
            for input_ in inputs
        )

    def convert_optional(
        self,
        input_: In | None
    ) -> Iterator[Out]:

        if input_ is None:
            return iter([])
        else:
            return self.convert(input_)

    def convert(self, input_: In) -> Iterator[Out]:
        return reduce(
            self.__convert_with,
            self.__converters,
            iter([input_])
        )

    def __convert_with(
        self,
        previous: Iterator[Any],
        converter: Converter
    ) -> Iterator[Any]:

        for p in previous:
            converted = converter.convert(p)

            if is_iter(converted):
                yield from converted
            else:
                yield converted

# not ideal, but this is a workaround
    def get_return_objects(self) -> Iterable[Out]:
        return []
