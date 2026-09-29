# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from dataclasses import dataclass


_REQUIRED = ('HOST', 'USERNAME', 'PASSWORD')


@dataclass(frozen=True, slots=True)
class RabbitmqConfig:
    """Configuration for connecting to RabbitMQ."""
    host: str
    port: int
    username: str
    password: str
    vhost: str
    exchange: str
    app_name: str = ''
    dlx: str = 'tol.dlx'
    use_ssl: bool = False
    write_batch_size: int = 100
    heartbeat: int = 60
    blocked_connection_timeout: float = 30.0
    socket_timeout: float = 10.0
    connection_attempts: int = 3
    retry_delay: float = 2.0
    ca_file: str | None = None

    @classmethod
    def from_env(cls, prefix: str = 'RABBITMQ_') -> 'RabbitmqConfig':
        missing = [
            f'{prefix}{name}' for name in _REQUIRED
            if not os.getenv(f'{prefix}{name}')
        ]
        if missing:
            raise ValueError(
                f'Missing required environment variable(s): '
                f'{", ".join(missing)}'
            )

        return cls(
            host=os.environ[f'{prefix}HOST'],
            port=int(os.getenv(f'{prefix}PORT', '5672')),
            username=os.environ[f'{prefix}USERNAME'],
            password=os.environ[f'{prefix}PASSWORD'],
            vhost=os.getenv(f'{prefix}VHOST', '/'),
            exchange=os.getenv(f'{prefix}EXCHANGE', 'tol'),
            use_ssl=os.getenv(f'{prefix}USE_SSL', 'false').lower() == 'true',
            write_batch_size=int(os.getenv(f'{prefix}WRITE_BATCH_SIZE', 100)),
            app_name=os.getenv(f'{prefix}APP_NAME', ''),
            dlx=os.getenv(f'{prefix}DLX', 'tol.dlx'),
            heartbeat=int(os.getenv(f'{prefix}HEARTBEAT', '60')),
            blocked_connection_timeout=float(
                os.getenv(f'{prefix}BLOCKED_CONNECTION_TIMEOUT', '30')
            ),
            socket_timeout=float(os.getenv(f'{prefix}SOCKET_TIMEOUT', '10')),
            connection_attempts=int(os.getenv(f'{prefix}CONNECTION_ATTEMPTS', '3')),
            retry_delay=float(os.getenv(f'{prefix}RETRY_DELAY', '2')),
            ca_file=os.getenv(f'{prefix}CA_FILE') or None,
        )
