# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.rabbitmq import RabbitmqConfig


@pytest.fixture(autouse=True)
def required_env(monkeypatch):
    """Set the variables from_env requires as the unit container has none."""
    monkeypatch.setenv('RABBITMQ_HOST', 'rabbitmq-host')
    monkeypatch.setenv('RABBITMQ_USERNAME', 'test-user')
    monkeypatch.setenv('RABBITMQ_PASSWORD', 'test-password')


class TestRequiredEnv:
    def test_reads_required(self):
        """Test that the required variables are read from the environment."""
        config = RabbitmqConfig.from_env()

        assert config.host == 'rabbitmq-host'
        assert config.username == 'test-user'
        assert config.password == 'test-password'

    @pytest.mark.parametrize('var', ['HOST', 'USERNAME', 'PASSWORD'])
    def test_missing_raises(self, monkeypatch, var):
        """Test that a missing required variable fails fast, naming it."""
        monkeypatch.delenv(f'RABBITMQ_{var}')

        with pytest.raises(ValueError, match=f'RABBITMQ_{var}'):
            RabbitmqConfig.from_env()

    def test_empty_counts_as_missing(self, monkeypatch):
        """Test that an empty value is treated as unset."""
        monkeypatch.setenv('RABBITMQ_HOST', '')

        with pytest.raises(ValueError, match='RABBITMQ_HOST'):
            RabbitmqConfig.from_env()


class TestRabbitmqConfigFromEnv:
    def test_default(self, monkeypatch):
        """
        Test that RabbitmqConfig.from_env() returns the expected
        default values when no environment variables are set.
        """
        for var in ('APP_NAME', 'DLX', 'EXCHANGE', 'DECLARE_EXCHANGES'):
            monkeypatch.delenv(f'RABBITMQ_{var}', raising=False)

        config = RabbitmqConfig.from_env()

        assert config.app_name == ''
        assert config.dlx == 'tol.dlx'
        assert config.exchange == 'tol'
        assert config.declare_exchanges is True

    def test_overrides(self, monkeypatch):
        monkeypatch.setenv('RABBITMQ_APP_NAME', 'portal')
        monkeypatch.setenv('RABBITMQ_DLX', 'custom.dlx')
        monkeypatch.setenv('RABBITMQ_DECLARE_EXCHANGES', 'false')

        config = RabbitmqConfig.from_env()

        assert config.app_name == 'portal'
        assert config.dlx == 'custom.dlx'
        assert config.declare_exchanges is False

    def test_connection_tuning_defaults(self, monkeypatch):
        """Connection tuning falls back to safe defaults."""
        for var in (
            'HEARTBEAT', 'BLOCKED_CONNECTION_TIMEOUT', 'SOCKET_TIMEOUT',
            'CONNECTION_ATTEMPTS', 'RETRY_DELAY', 'CA_FILE'
        ):
            monkeypatch.delenv(f'RABBITMQ_{var}', raising=False)

        config = RabbitmqConfig.from_env()

        assert config.heartbeat == 60
        assert config.blocked_connection_timeout == 30
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
