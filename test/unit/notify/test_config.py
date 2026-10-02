# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.notify import EmailConfig, SmtpSecurity


@pytest.fixture(autouse=True)
def required_env(monkeypatch):
    """Set the variables from_env requires."""
    monkeypatch.setenv('SMTP_HOST', 'smtp.example.com')
    monkeypatch.setenv('SMTP_FROM', 'noreply@example.com')
    for var in ('PORT', 'SECURITY', 'USERNAME', 'PASSWORD', 'TIMEOUT'):
        monkeypatch.delenv(f'SMTP_{var}', raising=False)


class TestFromEnv:
    def test_defaults(self):
        """Test that unset optional variables fall back to defaults."""
        config = EmailConfig.from_env()

        assert config.host == 'smtp.example.com'
        assert config.from_address == 'noreply@example.com'
        assert config.security is SmtpSecurity.STARTTLS
        assert config.port == 587
        assert config.username is None
        assert config.timeout == 30

    @pytest.mark.parametrize('var', ['HOST', 'FROM'])
    def test_missing_required_raises(self, monkeypatch, var):
        monkeypatch.delenv(f'SMTP_{var}')

        with pytest.raises(ValueError, match=f'SMTP_{var}'):
            EmailConfig.from_env()

    @pytest.mark.parametrize('security, port', [
        ('starttls', 587), ('ssl', 465), ('none', 25)
    ])
    def test_port_follows_security(self, monkeypatch, security, port):
        """Test that the default port matches the security mode."""
        monkeypatch.setenv('SMTP_SECURITY', security)

        assert EmailConfig.from_env().port == port

    def test_explicit_port_wins(self, monkeypatch):
        """Test that SMTP_PORT overridees the security default."""
        monkeypatch.setenv('SMTP_SECURITY', 'none')
        monkeypatch.setenv('SMTP_PORT', '1025')

        assert EmailConfig.from_env().port == 1025

    def test_unknown_security_raises(self, monkeypatch):
        """Test that an unknown SMTP_SECURITY value is rejected."""
        monkeypatch.setenv('SMTP_SECURITY', 'tls')

        with pytest.raises(ValueError):
            EmailConfig.from_env()


class TestValidation:
    def _config(self, **overrides):
        """Build an email config with optional overrides."""
        fields = {
            'host': 'smtp.example.com',
            'from_address': 'noreply@example.com',
            'port': 587
        }
        fields.update(overrides)
        return EmailConfig(**fields)

    @pytest.mark.parametrize('credentials', [
        {'username': 'user'}, {'password': 'secret'}
    ])
    def test_credentials_must_pair(self, credentials):
        """Test that username and password must be together."""
        with pytest.raises(ValueError, match='together'):
            self._config(**credentials)

    def test_credentials_refused_without_tls(self):
        """Test that credentials are never configured for plaintext SMTP."""
        with pytest.raises(ValueError, match='without TLS'):
            self._config(
                security=SmtpSecurity.NONE,
                username='user',
                password='secret'
            )

    def test_password_not_in_repr(self):
        """Test that the password deos not leak into logs."""
        config = self._config(username='username', password='secret')

        assert 'secret' not in repr(config)
