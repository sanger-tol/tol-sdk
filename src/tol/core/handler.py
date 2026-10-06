# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from .data_object import DataObject


class Handler(ABC):
    """
    Handles one message received by a `Consumer`.
    """

    @abstractmethod
    def handle(self, obj: DataObject) -> None:
        """Handle one received message."""
        raise NotImplementedError()
