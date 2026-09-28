# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.rabbitmq import RabbitmqConfig


class TestRabbitmqConfigFromEnv:
    def test_default(self, monkeypatch):
        """
        Test that RabbitmqConfig.from_env() returns the expected
        default values when no environment variables are set.
        """
        for var in ('APP_NAME', 'DLX', 'EXCHANGE'):
            monkeypatch.delenv(f'RABBITMQ_{var}', raising=False)

        config = RabbitmqConfig.from_env()

        assert config.app_name == ''
        assert config.dlx == 'tol.dlx'
        assert config.exchange == 'tol'

    def test_overrides(self, monkeypatch):
        monkeypatch.setenv('RABBITMQ_APP_NAME', 'portal')
        monkeypatch.setenv('RABBITMQ_DLX', 'custom.dlx')

        config = RabbitmqConfig.from_env()

        assert config.app_name == 'portal'
        assert config.dlx == 'custom.dlx'

    def test_connection_tuning_defaults(self, monkeypatch):
        """Connection tuning falls back to safe defaults."""
        for var in (
            'HEARTBEAT', 'BLOCKED_CONNECTION_TIMEOUT', 'SOCKET_TIMEOUT',
            'CONNECTION_ATTEMPTS', 'RETRY_DELAY', 'CA_FILE'
        ):
            monkeypatch.delenv(f'RABBITMQ_{var}', raising=False)

        config = RabbitmqConfig.from_env()

        assert config.heartbeat == 60
        assert config.blocked_connection_timeout == 36
        assert config.socket_timeout == 10
        assert config.connection_attempts == 3
        assert config.retry_delay == 2
        assert config.ca_file is None

    def test_connection_tuning_overrides(self, monkeypatch):
        monkeypatch.setenv('RABBITMQ_HEARTBEAT', '30')
        monkeypatch.setenv('RABBITMQ_CA_FILE', '/certs/ca.pem')

        config = RabbitmqConfig.from_env()

        assert config.heartbeat == 30
        assert config.ca_file == '/certs/ca.pem'
