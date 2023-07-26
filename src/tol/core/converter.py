# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Generic, Iterable, Optional, TypeVar


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
