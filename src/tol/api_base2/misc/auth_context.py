# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional


class AuthContext:
    """
    The auth context for a specific request, lasting
    only for its duration.

    Used principally to store the ID for the user making
    a request, if authenticated, but can also be used for
    other things.
    """

    def __init__(self) -> None:
        self.__user_id: Optional[str] = None

    @property
    def user_id(self) -> Optional[str]:
        """
        A `str` that uniquely identifies a user, if
        authenticated.
        """
        return self.__user_id

    @user_id.setter
    def user_id(self, val: str) -> None:
        self.__user_id = val
