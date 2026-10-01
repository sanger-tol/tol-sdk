# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from dataclasses import dataclass


_REQUIRED = ('HOST', 'USERNAME', 'PASSWORD')


@dataclass(frozen=True, slots=True)
class RabbitmqConfig:
    """Configuration for connecting to RabbitMQ.

    Attributes:
        host (str): RabbitMQ broker hostname or IP address.
        port (int): AMQP port to connect to, typically 5672.
        username (str): Account name used to authenticate to RabbitMQ.
        password (str): Password corresponding to ``username``.
        vhost (str): Virtual host namespace to connect to, usually ``/``.
        exchange (str): Default exchange name used for publishing messages.
        app_name (str): Optional application name reported in client metadata.
        dlx (str): Dead-letter exchange name used when messages are rejected or
            expired.
        use_ssl (bool): Whether TLS/SSL should be enabled for the connection.
        write_batch_size (int): Number of messages to buffer before flushing a
            batch.
        heartbeat (int): Server/client heartbeat interval in seconds to detect
            dead connections.
        blocked_connection_timeout (float): Maximum time in seconds that a
            connection may remain blocked before timing out.
        socket_timeout (float): Timeout in seconds for socket read/write
            operations.
        connection_attempts (int): Number of times to retry establishing a
            connection.
        retry_delay (float): Delay in seconds between retry attempts.
        ca_file (str | None): Optional path to a CA certificate file for TLS
            verification.
        declare_exchanges (bool): Whether required exchanges should be declared on
            the broker automatically when the client starts.
    """
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
    declare_exchanges: bool = True

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
            declare_exchanges=os.getenv(
                f'{prefix}DECLARE_EXCHANGES', 'true'
            ).lower() == 'true'
        )
