# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..core import DataSource


class Action(ABC):
    """
    The central class for running local actions.
    """

    @abstractmethod
    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, bool], int]:
        """
        Run the action on the given IDs and return status in
        format ({'success': True}, 200).
        """

        pass
