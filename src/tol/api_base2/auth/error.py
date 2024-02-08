# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


class AuthError(Exception):
    """The custom `Exception` class for Auth problems."""

    def __init__(
        self,
        status_code: int = 500,
        title: str = 'Unknown Error',
        detail: str = 'An unknown error occured.'
    ) -> None:

        self.__code = status_code
        self.__title = title
        self.__detail = detail

    @property
    def status_code(self) -> int:
        return self.__code

    @property
    def errors(self) -> list[dict[str, str]]:
        return [
            {
                'title': self.__title,
                'detail': self.__detail
            }
        ]


class StateNotFoundError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            400,
            'Unknown State',
            'The given state UUID is not recognised.'
        )
