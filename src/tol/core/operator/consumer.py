# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any


class Consumer(ABC):
    """
    Consumes messages, passing each to the `Handler` configured
    for its message type.
    """

    @abstractmethod
    def consume(
        self,
        handlers: dict[str, dict[str, Any]],
        **kwargs: Any
    ) -> None:
        """
        Build one handler per message type from its
        `{'module', 'class_name', 'config_details'}` spec, then consume.
        """
        raise NotImplementedError()
