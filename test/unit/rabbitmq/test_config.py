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
