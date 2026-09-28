# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RabbitmqConfig:
    """Configuration for connecting to RabbitMQ."""
    host: str
    port: int
    username: str
    password: str
    vhost: str
    exchange: str
    management_url: str
    app_name: str = ''
    dlx: str = 'tol.dlx'
    use_ssl: bool = False
    write_batch_size: int = 100
    heartbeat: int = 60
    blocked_connection_timeout: float = 36.0
    socket_timeout: float = 10.0
    connection_attempts: int = 3
    retry_delay: float = 2.0
    ca_file: str | None = None

    @classmethod
    def from_env(cls, prefix: str = 'RABBITMQ_') -> 'RabbitmqConfig':
        return cls(
            host=os.getenv(f'{prefix}HOST', '127.0.0.1'),
            port=int(os.getenv(f'{prefix}PORT', '5672')),
            username=os.getenv(f'{prefix}USERNAME', 'guest'),
            password=os.getenv(f'{prefix}PASSWORD', 'guest'),
            vhost=os.getenv(f'{prefix}VHOST', '/'),
            exchange=os.getenv(f'{prefix}EXCHANGE', 'tol'),
            management_url=os.getenv(f'{prefix}MANAGEMENT_URL',
                                     'http://127.0.0.1:15672'),
            use_ssl=os.getenv(f'{prefix}USE_SSL', 'false').lower() == 'true',
            write_batch_size=int(os.getenv(f'{prefix}WRITE_BATCH_SIZE', 100)),
            app_name=os.getenv(f'{prefix}APP_NAME', ''),
            dlx=os.getenv(f'{prefix}DLX', 'tol.dlx'),
            heartbeat=int(os.getenv(f'{prefix}HEARTBEAT', '60')),
            blocked_connection_timeout=float(
                os.getenv(f'{prefix}BLOCKED_CONNECTION_TIMEOUT', '36')
            ),
            socket_timeout=float(os.getenv(f'{prefix}SOCKET_TIMEOUT', '10')),
            connection_attempts=int(os.getenv(f'{prefix}CONNECTION_ATTEMPTS', '3')),
            retry_delay=float(os.getenv(f'{prefix}RETRY_DELAY', '2')),
            ca_file=os.getenv(f'{prefix}CA_FILE') or None,
        )
