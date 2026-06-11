import pytest
from unittest.mock import MagicMock
from tol.sources.registry import DataSourceRegistry, SourceDefinition, EnvVar


class TestEnvVar:
    def test_resolve_returns_env_value(self, monkeypatch):
        monkeypatch.setenv('MY_URL', 'http://test.com')
        assert EnvVar('MY_URL').resolve() == 'http://test.com'


def test_resolve_returns_default_when_unset(self):
    assert EnvVar('UNSET_VAR', 'fallback').resolve() == 'fallback'

def test_resolve_returns_none_when_unset_no_default(self):
    assert EnvVar('UNSET_VAR').resolve() is None

class TestSourceDefinition:
    def test_resolve_maps_env_vars_to_kwargs(self, monkeypatch):
        monkeypatch.setenv('URL', 'http://x.com')
        defn = SourceDefinition(
            factory=lambda api_url, token: None,
            env_mapping={
                'api_url': EnvVar('URL'),
                'token': EnvVar('TOKEN_VAR'),
            },
        )
        result = defn.resolve()
        assert result['api_url'] == 'http://x.com'
        assert result['token'] is None


def test_resolve_applies_overrides(self):
    defn = SourceDefinition(
        factory=lambda api_url: None,
        env_mapping={'api_url': EnvVar('X', 'default')},
    )
    assert defn.resolve(api_url='http://override.com')['api_url'] == 'http://override.com'

def test_resolve_composes_args(self, monkeypatch):
    monkeypatch.setenv('URL', 'http://test.com')
    monkeypatch.setenv('PATH', '/api/v1')
    defn = SourceDefinition(
        factory=lambda api_url: None,
        env_mapping={'url': EnvVar('URL'), 'api_path': EnvVar('PATH')},
        compose_args={'api_url': ['url', 'api_path']},
    )
    assert defn.resolve()['api_url'] == 'http://test.com/api/v1'

def test_resolve_merges_defaults(self):
    defn = SourceDefinition(
        factory=lambda retries: None,
        defaults={'retries': 5},
    )
    assert defn.resolve()['retries'] == 5

class TestDataSourceRegistry:
    def test_create_unknown_source_raises(self):
        reg = DataSourceRegistry()
        with pytest.raises(KeyError, match="Unknown source"):
            reg.create('nonexistent')


def test_available_sources(self):
    reg = DataSourceRegistry()
    mock_factory = MagicMock()
    reg.register('portal', SourceDefinition(factory=mock_factory))
    assert 'portal' in reg.available_sources

def test_create_calls_factory_with_resolved_kwargs(self, monkeypatch):
    monkeypatch.setenv('MY_URL', 'http://test.com')
    mock_factory = MagicMock()
    reg = DataSourceRegistry()
    reg.register('test', SourceDefinition(
        factory=mock_factory,
        env_mapping={'api_url': EnvVar('MY_URL')},
    ))
    reg.create('test')
    mock_factory.assert_called_once_with(api_url='http://test.com')

def test_create_passes_overrides_to_factory(self):
    mock_factory = MagicMock()
    reg = DataSourceRegistry()
    reg.register('test', SourceDefinition(factory=mock_factory))
    reg.create('test', retries=10)
    mock_factory.assert_called_once_with(retries=10)