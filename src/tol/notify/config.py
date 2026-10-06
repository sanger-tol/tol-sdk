# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from dataclasses import dataclass, field
from enum import StrEnum

_REQUIRED = ('HOST', 'FROM')


class SmtpSecurity(StrEnum):
    STARTTLS = 'starttls'
    SSL = 'ssl'
    NONE = 'none'


_DEFAULT_PORTS = {
    SmtpSecurity.STARTTLS: 587,
    SmtpSecurity.SSL: 465,
    SmtpSecurity.NONE: 25
}


@dataclass(frozen=True, slots=True)
class EmailConfig:
    """Config for sending email over SMTP"""
    host: str
    from_address: str
    port: int
    security: SmtpSecurity = SmtpSecurity.STARTTLS
    username: str | None = None
    password: str | None = field(default=None, repr=False)  # hide in logs
    timeout: float = 30.0

    def __post_init__(self) -> None:
        # Raise if exactly one of these is true
        if (self.username is None) != (self.password is None):
            raise ValueError(
                'SMTP username and password must be set together'
            )
        if self.username is not None and self.security is SmtpSecurity.NONE:
            raise ValueError(
                'Refusing to send SMTP credentials without TLS '
                '(security is "none")'
            )

    @classmethod
    def from_env(cls, prefix: str = 'SMTP_') -> 'EmailConfig':
        missing = [
            f'{prefix}{name}' for name in _REQUIRED
            if not os.getenv(f'{prefix}{name}')
        ]
        if missing:
            raise ValueError(
                f'Missing required environment variable(s): '
                f'{", ".join(missing)}'
            )

        security = SmtpSecurity(
            os.getenv(f'{prefix}SECURITY', 'starttls').lower()
        )

        port = os.getenv(f'{prefix}PORT')

        return cls(
            host=os.environ[f'{prefix}HOST'],
            from_address=os.environ[f'{prefix}FROM'],
            port=int(port) if port else _DEFAULT_PORTS[security],
            security=security,
            username=os.getenv(f'{prefix}USERNAME', None),
            password=os.getenv(f'{prefix}PASSWORD', None),
            timeout=float(os.getenv(f'{prefix}TIMEOUT', '30'))
        )
