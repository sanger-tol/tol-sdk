# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional


class ActionParameters:
    """
    Parses the parameters from a query string for a Action POST
    endpoint.
    """

    def __init__(self, request_args: Dict[str, str]) -> None:
        self.__request_args = request_args

    @property
    def action_name(self) -> str:  # noqa A003
        """
        The optional action name.
        """
        return self.__request_args.get('action_name')

    @property
    def ids(self) -> list[str]:  # noqa A003
        """
        The action IDs.
        """
        return self.__request_args.get('ids')

    @property
    def params(self) -> Optional[dict[str, Any]]:  # noqa A003
        """
        The optional action parameters.
        """
        if self.__request_args.get('params') is None:
            return {}
        return self.__request_args.get('params')
