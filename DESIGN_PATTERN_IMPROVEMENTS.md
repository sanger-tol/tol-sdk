# Design Pattern Improvements

---

## 1. DataSource Registry

**Pattern type:** Creational (Abstract Factory / Registry)

### Current pattern

~30 files in `src/tol/sources/` repeat the same 3-step ceremony: read env vars, construct a DataSource, call `core_data_object()`, return. Three variants exist:

**API sources** (portal, sts, tolid, tolqc, bioscan, treeofsex, workflows, portaldb):

```python
# src/tol/sources/portal.py
def portal(retries=5, dataspace='tol_production', **kwargs):
    portal = create_api_datasource(
        api_url=os.getenv('PORTAL_URL', Defaults.PORTAL_URL)
        + os.getenv('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
        token=os.getenv('PORTAL_API_KEY'),
        data_prefix=os.getenv('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH)
        + f'/{dataspace}',
        retries=retries
    )
    core_data_object(portal)
    return portal
```

**Service sources** (bold, goat, copo, labwhere, ena, jira/grit):

```python
# src/tol/sources/bold.py
def bold(**kwargs):
    bold = create_bold_datasource(
        bold_url=os.getenv('BOLD_URL', Defaults.BOLD_URL)
        + os.getenv('BOLD_API_PATH', Defaults.BOLD_API_PATH),
        bold_portal_url=os.getenv('BOLD_PORTAL_URL', Defaults.BOLD_PORTAL_URL)
        + os.getenv('BOLD_API_PATH', Defaults.BOLD_API_PATH),
        bold_api_key=os.getenv('BOLD_API_KEY')
    )
    core_data_object(bold)
    return bold
```

**Config-dict sources** (benchling, mlwh, sciops, sts_legacy, google sheets):

```python
# src/tol/sources/benchling.py
def benchling(**kwargs):
    benchling = BenchlingDataSource({
        'api_key': os.getenv('BENCHLING_API_KEY'),
        'url': os.getenv('BENCHLING_URL'),
        'registry_id': os.getenv('BENCHLING_REGISTRY_ID'),
        'project_id': os.getenv('BENCHLING_PROJECT_ID')
    })
    core_data_object(benchling)
    return benchling
```

### Changes required

Create `src/tol/sources/registry.py`:

```python
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from tol.core import core_data_object
from tol.core.datasource import DataSource


@dataclass(frozen=True)
class EnvVar:
    """A reference to an environment variable with an optional default."""
    name: str
    default: str | None = None

    def resolve(self) -> str | None:
        return os.getenv(self.name, self.default)


@dataclass(frozen=True)
class SourceDefinition:
    """Declarative definition of how to create a DataSource."""
    factory: Callable[..., DataSource]
    env_mapping: dict[str, EnvVar] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    compose_args: dict[str, list[str]] | None = None

    def resolve(self, **overrides: Any) -> dict[str, Any]:
        resolved = {}
        for kwarg_name, env_var in self.env_mapping.items():
            resolved[kwarg_name] = env_var.resolve()
        resolved.update(self.defaults)
        if self.compose_args:
            for target, parts in self.compose_args.items():
                resolved[target] = ''.join(
                    str(resolved.pop(p, '') or '') for p in parts
                )
        resolved.update(overrides)
        return resolved


class DataSourceRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, SourceDefinition] = {}

    def register(self, name: str, definition: SourceDefinition) -> None:
        self._definitions[name] = definition

    @property
    def available_sources(self) -> list[str]:
        return list(self._definitions.keys())

    def create(self, name: str, **overrides: Any) -> DataSource:
        if name not in self._definitions:
            raise KeyError(
                f"Unknown source: '{name}'. Available: {self.available_sources}"
            )
        defn = self._definitions[name]
        kwargs = defn.resolve(**overrides)
        ds = defn.factory(**kwargs)
        core_data_object(ds)
        return ds
```

Register API sources declaratively in `src/tol/sources/_api_sources.py`:

```python
from tol.api_client import create_api_datasource
from .defaults import Defaults
from .registry import DataSourceRegistry, SourceDefinition, EnvVar

def register_api_sources(registry: DataSourceRegistry) -> None:
    api_sources = {
        'portal': {
            'url': EnvVar('PORTAL_URL', Defaults.PORTAL_URL),
            'api_path': EnvVar('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
            'token': EnvVar('PORTAL_API_KEY'),
            'data_prefix': EnvVar('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH),
        },
        'sts': {
            'url': EnvVar('STS_URL', Defaults.STS_URL),
            'api_path': EnvVar('STS_API_PATH', Defaults.STS_API_PATH),
            'token': EnvVar('STS_API_KEY'),
            'data_prefix': EnvVar('STS_API_DATA_PATH', Defaults.STS_API_DATA_PATH),
        },
        # tolid, tolqc, bioscan, treeofsex, workflows, portaldb...
    }
    for name, env_map in api_sources.items():
        registry.register(name, SourceDefinition(
            factory=create_api_datasource,
            env_mapping=env_map,
            defaults={'retries': 5},
            compose_args={'api_url': ['url', 'api_path']},
        ))
```

Keep existing functions as thin backward-compatible wrappers:

```python
# src/tol/sources/portal.py
from .registry import default_registry

def portal(retries=5, dataspace='tol_production', **kwargs):
    return default_registry.create(
        'portal', retries=retries, data_prefix_suffix=f'/{dataspace}', **kwargs
    )
```

Usage:

```python
# Before
from tol.sources.portal import portal
ds = portal(retries=3)

# After
from tol.sources import registry
ds = registry.create('portal', retries=3)

# Override URL for testing
ds = registry.create('portal', api_url='http://localhost:8000/api/v1')
```

### Benefits

- Eliminates duplication across ~30 near-identical files
- Env var resolution is centralised and testable in one place
- Sources become discoverable at runtime via `registry.available_sources`
- URLs/credentials can be overridden without env vars

### Testing impact

There is currently no `test/unit/sources/` directory — none of the 30 source files have unit tests. They are only exercised indirectly by integration tests that require real env vars and live services.

### Testability improvement

The registry separates env var resolution from DataSource construction, making both independently testable without env vars or network access.

### How to write the tests

```python
# test/unit/sources/test_registry.py
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
```

---

## 2. Typed DataSource Configuration

**Pattern type:** Creational (Builder)

### Current pattern

`DataSource.__init__()` in `src/tol/core/datasource.py` takes a `Dict[str, Any]` and uses `setattr` to splat keys onto the instance:

```python
DataSourceConfig = Dict[str, Any]

class DataSource(ABC):
    def __init__(self, config: DataSourceConfig, *args, expected=None, **kwargs):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    def __validate_config(self, config, expected):
        if expected is None:
            return
        for k in expected:
            if k not in config:
                raise DataSourceError(
                    title='Incorrect configuration',
                    detail=f'{k} missing in config dict'
                )
```

Eight DataSource subclasses use this config dict pattern:

| DataSource | Expected keys | Type safety |
|---|---|---|
| `BenchlingDataSource` | `url`, `api_key`, `registry_id`, `project_id` | None |
| `MlwhDataSource` | `uri` | None |
| `SequencingDataSource` | 13 keys (rabbitmq config) | None |
| `StsDataSource` | `url`, `key` | None |
| `GoogleSheetDataSource` | `client_secrets`, `sheet_key`, `mappings` | None |
| `ElasticDataSource` | `uri`, `user`, `password`, `index_prefix` | None |
| `JsonDataSource` | `uri`, `type`, `id_attribute`, `mappings` | None |
| `S3JsonDataSource` | 7 keys | None |

Validation only checks key presence. Wrong value types, empty strings, and `None` values all pass silently:

```python
# All of these pass validation — fail later at runtime
BenchlingDataSource({'url': 123, 'api_key': None, 'registry_id': '', 'project_id': ''})
SequencingDataSource({'rabbitmq_port': 'not-a-number', ...})
```

The `setattr` loop can overwrite methods or properties if a config key collides with them.

### Changes required

**Step 1** — Create a frozen dataclass per DataSource that uses config dicts:

```python
# src/tol/benchling/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class BenchlingConfig:
    url: str
    api_key: str
    registry_id: str
    project_id: str
```

```python
# src/tol/sciops/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class SciopsConfig:
    redpanda_url: str
    redpanda_api_key: str
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_username: str
    rabbitmq_password: str
    rabbitmq_vhost: str
    rabbitmq_exchange: str
    rabbitmq_routing_key: str
    rabbitmq_use_ssl: bool = False
    rabbitmq_publish_retry_delay: int = 5
    rabbitmq_publish_retries: int = 3
    tol_feedback_queue: str = ''
```

```python
# src/tol/mlwh/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MlwhConfig:
    uri: str
```

Repeat for `GoogleSheetConfig`, `ElasticConfig`, `JsonConfig`, `S3JsonConfig`, `StsLegacyConfig`.

**Step 2** — Update `DataSource.__init__` to accept both patterns (backward compatible):

```python
# src/tol/core/datasource.py
class DataSource(ABC):
    def __init__(self, config: DataSourceConfig | object, *args,
                 expected: list[str] | None = None,
                 attribute_metadata=DefaultAttributeMetadata, **kwargs):
        self.__data_object_factory = None
        self.__attribute_metadata = attribute_metadata

        if isinstance(config, dict):
            # Legacy dict path — unchanged
            self.__validate_config(config, expected)
            for k, v in config.items():
                setattr(self, k, v)
        else:
            # New typed config path
            from dataclasses import fields
            for f in fields(config):
                setattr(self, f.name, getattr(config, f.name))
```

**Step 3** — Update each DataSource subclass to accept both:

```python
# src/tol/benchling/benchling_datasource.py
from .config import BenchlingConfig

class BenchlingDataSource(DataSource, ...):
    def __init__(self, config: BenchlingConfig | DataSourceConfig, ...):
        if isinstance(config, dict):
            config = BenchlingConfig(**config)  # Convert legacy dict
        super().__init__(config)
```

**Step 4** — Update sources to use typed configs:

```python
# src/tol/sources/benchling.py
from tol.benchling.config import BenchlingConfig

def benchling(**kwargs):
    cfg = BenchlingConfig(
        api_key=os.getenv('BENCHLING_API_KEY'),
        url=os.getenv('BENCHLING_URL'),
        registry_id=os.getenv('BENCHLING_REGISTRY_ID'),
        project_id=os.getenv('BENCHLING_PROJECT_ID'),
    )
    ds = BenchlingDataSource(cfg)
    core_data_object(ds)
    return ds
```

Files that need changes:

| File | Change |
|---|---|
| `src/tol/core/datasource.py` | Add dataclass branch to `__init__` |
| `src/tol/benchling/config.py` | New file |
| `src/tol/sciops/config.py` | New file |
| `src/tol/mlwh/config.py` | New file |
| One new config file per config-dict DataSource | New files |
| Each config-dict DataSource `__init__` | Accept both patterns |

### Benefits

- Missing or mistyped keys cause `TypeError` at construction, not deep runtime errors
- Wrong value types are caught early (e.g. `rabbitmq_port` must be `int`)
- IDE autocompletion and type checking work on config fields
- Config objects are frozen — cannot be accidentally mutated
- `setattr` collision risk eliminated for typed path
- Self-documenting: each config dataclass declares exactly what a DataSource needs

### Testing impact

All existing tests pass without changes because the dict path is preserved. Tests that construct DataSources with dicts (e.g. `_TestDataSourceExpected({'field1': 'v1', 'field2': 'v2'})` in `test/unit/core/test_datasource.py`) continue to work.

### Testability improvement

Config objects can be validated independently of DataSource construction. Invalid configurations are caught by the type system. Tests no longer need to verify runtime config dict key expectations — the dataclass constructor enforces them.

### How to write the tests

```python
# test/unit/benchling/test_config.py
import pytest
from dataclasses import FrozenInstanceError
from tol.benchling.config import BenchlingConfig


class TestBenchlingConfig:
    def test_valid_config(self):
        cfg = BenchlingConfig(
            url='https://x.benchling.com',
            api_key='sk-abc123',
            registry_id='src_abc',
            project_id='src_xyz',
        )
        assert cfg.url == 'https://x.benchling.com'
        assert cfg.api_key == 'sk-abc123'

    def test_missing_required_field_raises_type_error(self):
        with pytest.raises(TypeError):
            BenchlingConfig(url='https://x.benchling.com')

    def test_unexpected_field_raises_type_error(self):
        with pytest.raises(TypeError):
            BenchlingConfig(
                url='https://x', api_key='k',
                registry_id='r', project_id='p',
                not_a_field='oops',
            )

    def test_frozen_prevents_mutation(self):
        cfg = BenchlingConfig(
            url='https://x', api_key='k',
            registry_id='r', project_id='p',
        )
        with pytest.raises(FrozenInstanceError):
            cfg.url = 'https://other'


# test/unit/sciops/test_config.py
from tol.sciops.config import SciopsConfig


class TestSciopsConfig:
    def test_required_fields(self):
        cfg = SciopsConfig(
            redpanda_url='http://x', redpanda_api_key='k',
            rabbitmq_host='host', rabbitmq_port=5672,
            rabbitmq_username='u', rabbitmq_password='p',
            rabbitmq_vhost='/', rabbitmq_exchange='ex',
            rabbitmq_routing_key='rk',
        )
        assert cfg.rabbitmq_port == 5672
        assert cfg.rabbitmq_use_ssl is False  # default

    def test_defaults_applied(self):
        cfg = SciopsConfig(
            redpanda_url='http://x', redpanda_api_key='k',
            rabbitmq_host='host', rabbitmq_port=5672,
            rabbitmq_username='u', rabbitmq_password='p',
            rabbitmq_vhost='/', rabbitmq_exchange='ex',
            rabbitmq_routing_key='rk',
        )
        assert cfg.rabbitmq_publish_retry_delay == 5
        assert cfg.rabbitmq_publish_retries == 3
        assert cfg.tol_feedback_queue == ''


# test/unit/core/test_datasource.py — add to existing file
class TestDataSourceTypedConfig:
    def test_typed_config_sets_attributes(self):
        """DataSource accepts a dataclass config and sets attributes."""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class TestConfig:
            field1: str
            field2: str

        class _DS(DataSource):
            def __init__(self, config):
                super().__init__(config)

            @property
            def supported_types(self):
                return []

        ds = _DS(TestConfig(field1='a', field2='b'))
        assert ds.field1 == 'a'
        assert ds.field2 == 'b'

    def test_dict_config_still_works(self):
        """Legacy dict config path is unchanged."""
        ds = _TestDataSourceExpected({'field1': 'v1', 'field2': 'v2'})
        assert ds.field1 == 'v1'


# test/unit/benchling/test_benchling_datasource.py — add to existing
class TestBenchlingDataSourceConfig:
    def test_accepts_typed_config(self):
        cfg = BenchlingConfig(
            url='https://x', api_key='k',
            registry_id='r', project_id='p',
        )
        ds = BenchlingDataSource(cfg)
        assert ds.url == 'https://x'

    def test_accepts_legacy_dict(self):
        ds = BenchlingDataSource({
            'url': 'https://x', 'api_key': 'k',
            'registry_id': 'r', 'project_id': 'p',
        })
        assert ds.url == 'https://x'
```

---

## 3. CoreDataObject Dependency Injection

**Pattern type:** Structural (Dependency Injection, replacing closure-based composition)

### Current pattern

`core_data_object()` in `src/tol/core/factory.py` defines a **new class inside the function body** on every call, capturing the DataSource lookup dict via closure:

```python
def core_data_object(
    *data_sources: DataSource,
    one_dict_factory=lambda o: ToOneDict(o),
    many_dict_factory=lambda o: ToManyDict(o),
    data_source_dict_factory=lambda *d: DataSourceDict(*d),
) -> type[DataObject]:

    data_source_dict = data_source_dict_factory(*data_sources)

    class CoreDataObject(DataObject, ABC):
        # 150+ line class defined inside the function
        # References data_source_dict via closure

        def __unstub(self):
            data_source_dict[t].get_one(t, self.__id)  # closure reference

        @property
        def _host(self):
            return data_source_dict[self.type]  # closure reference

    def core_data_object_factory(type_, id_=None, ...):
        return CoreDataObject(type_, id_=id_, ...)

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return CoreDataObject
```

Problems:

1. **Each call creates a different type** — `isinstance` fails across DataSource boundaries:
   ```python
   ClassA = core_data_object(ds1)
   ClassB = core_data_object(ds2)
   isinstance(ClassA('x', id_='1'), ClassB)  # False
   ```

2. **Closure hides state** — `data_source_dict` cannot be inspected, replaced, or mocked in tests.

3. **Factory injection requires a workaround** — `conftest.py` overwrites the factory immediately after it's set:
   ```python
   mdo = core_data_object(mock_ds)
   mock_ds.data_object_factory = mdo  # overwrites what core_data_object just set
   ```

4. **`CoreDataObject` cannot be imported** — it only exists inside the function scope. Type hints must use `DataObject` instead.

5. **Class inherits `ABC` but is instantiated directly** — misleading.

### Changes required

Extract `CoreDataObject` to module level with an explicit registry dict instead of a closure. `core_data_object()` keeps the same signature and return type.

Replace the contents of `src/tol/core/factory.py`:

```python
from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from typing import Any, Protocol

from .data_object import DataDict, DataObject
from .data_source_dict import DataSourceDict
from .datasource_error import DataSourceError, NotRelationalError
from .operator import Relational
from .relationship import RelationshipConfig, ToManyDict, ToOneDict

if typing.TYPE_CHECKING:
    from .datasource import DataSource


ToOne = dict[str, DataObject | None]
ToMany = dict[str, Iterable[DataObject]]


class DataObjectFactory(Protocol):
    def __call__(
        self, type_: str, id_: str | None = None,
        attributes: dict[str, Any] | None = None,
        to_one: ToOne | None = None,
        to_many: ToMany | None = None,
    ) -> DataObject: ...


class DataSourceDictFactory(Protocol):
    def __call__(self, *data_sources: DataSource) -> dict[str, DataSource]: ...


OneDictFactory = Callable[[DataObject], dict[str, DataObject | None]]
ManyDictFactory = Callable[[DataObject], dict[str, Iterable[DataObject]]]


def _local_name(__name: str) -> bool:
    __PROPERTY_NAMES = [
        'id', 'type', 'provenance', 'attributes',
        'to_one_relationships', 'to_many_relationships', 'get_field_by_name',
    ]
    return __name.startswith('_') or __name in __PROPERTY_NAMES


# Module-level registry — replaces the closure-captured data_source_dict
_data_source_registry: dict[str, DataSource] = {}
_one_dict_factory: OneDictFactory = lambda o: ToOneDict(o)
_many_dict_factory: ManyDictFactory = lambda o: ToManyDict(o)


class CoreDataObject(DataObject):
    """
    A DataObject that can be created outside of a DataSource.
    Resolves its hosting DataSource from the module-level registry.
    """

    def __init__(
        self, type_: str, id_: str | None = None,
        provenance_: str | None = None,
        attributes: DataDict | None = None,
        to_one: ToOne | None = None,
        to_many: ToMany | None = None,
        stub: bool = False,
        stub_types: Iterable[str] | None = None,
    ):
        self.__id = id_
        self.__type = type_
        self.__provenance = provenance_
        self.__attributes = {} if attributes is None else attributes
        self.__to_one_objects = {} if to_one is None else to_one
        self.__to_many_objects = {} if to_many is None else to_many
        if stub and id_ is None:
            raise DataSourceError('ID must be set if stub is True')
        self.__stub_value = stub
        self.__stub_types = stub_types
        if self.__relational:
            self.__to_one_relations = _one_dict_factory(self)
            self.__to_many_relations = _many_dict_factory(self)

    def __str__(self) -> str:
        dump = f'type="{self.type}"'
        if self.id is not None:
            dump += f', id="{self.id}"'
        return f'CoreDataObject({dump})'

    def __getattribute__(self, name: str, /) -> Any:
        if _local_name(name):
            return object.__getattribute__(self, name)
        if self.__stub_value:
            self.__unstub()
        if name in self.__to_one_names:
            if name in self._to_one_objects:
                return self._to_one_objects[name]
            return self.to_one_relationships.get(name)
        if name in self.__to_many_names:
            if name in self._to_many_objects:
                return self._to_many_objects[name]
            return self.to_many_relationships.get(name, [])
        return self.__attributes.get(name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        if _local_name(name):
            object.__setattr__(self, name, value)
        elif name in self.__to_one_names:
            self._to_one_objects[name] = value
        elif name in self.__to_many_names:
            self._to_many_objects[name] = value
        else:
            self.__attributes[name] = value

    def __unstub(self) -> None:
        self.__stub_value = False
        possible_types = (
            self.__stub_types if self.__stub_types is not None
            else [self.__type]
        )
        for t in possible_types:
            obj = _data_source_registry[t].get_one(t, self.__id)
            if obj is not None:
                self.__type = obj.type
                self.__attributes = obj.attributes
                self.__to_one_objects = obj._to_one_objects
                break

    @property
    def type(self) -> str:
        if self.__stub_value and self.__type is None:
            self.__unstub()
        return self.__type

    @property
    def id(self) -> str | None:
        return self.__id

    @id.setter
    def id(self, new_id: str) -> None:
        self.__id = new_id

    @property
    def provenance(self) -> str | None:
        return self.__provenance

    @provenance.setter
    def provenance(self, new_provenance: str | None) -> None:
        self.__provenance = new_provenance

    @property
    def attributes(self) -> dict[str, Any]:
        if self.__stub_value:
            self.__unstub()
        return self.__attributes

    @property
    def to_one_relationships(self) -> dict[str, DataObject | None]:
        if not self.__relational:
            raise NotRelationalError(self)
        return self.__to_one_relations

    @property
    def to_many_relationships(self) -> dict[str, list[DataObject]]:
        if not self.__relational:
            raise NotRelationalError(self)
        return self.__to_many_relations

    @property
    def _to_one_objects(self) -> dict[str, DataObject | None]:
        return self.__to_one_objects

    @property
    def _to_many_objects(self) -> dict[str, list[DataObject]]:
        return self.__to_many_objects

    @property
    def __relational(self) -> bool:
        return isinstance(self._host, Relational)

    @property
    def __relationship_config(self) -> RelationshipConfig | None:
        return self._host.relationship_config.get(self.type)

    @property
    def __to_one_names(self) -> list[str]:
        if not self.__relational:
            return []
        cfg = self.__relationship_config
        return (
            [] if cfg is None or cfg.to_one is None
            else list(cfg.to_one.keys())
        )

    @property
    def __to_many_names(self) -> list[str]:
        if not self.__relational:
            return []
        cfg = self.__relationship_config
        return (
            [] if cfg is None or cfg.to_many is None
            else list(cfg.to_many.keys())
        )

    @property
    def _host(self) -> DataSource | Relational:
        return _data_source_registry[self.type]


def core_data_object(
    *data_sources: DataSource,
    one_dict_factory: OneDictFactory = lambda o: ToOneDict(o),
    many_dict_factory: ManyDictFactory = lambda o: ToManyDict(o),
    data_source_dict_factory: DataSourceDictFactory = lambda *d: DataSourceDict(*d),
) -> type[DataObject]:
    """
    Register DataSources and return the CoreDataObject class.

    Same external API as before — takes datasources, returns a class,
    and injects factories. Now backed by a single CoreDataObject class
    with an explicit registry.
    """
    global _one_dict_factory, _many_dict_factory
    _one_dict_factory = one_dict_factory
    _many_dict_factory = many_dict_factory

    ds_dict = data_source_dict_factory(*data_sources)
    _data_source_registry.update(ds_dict)

    def _factory(
        type_: str, id_: str | None = None,
        attributes: dict[str, Any] | None = None,
        to_one: ToOne | None = None,
        to_many: ToMany | None = None,
        stub: bool = False,
        stub_types: Iterable[str] | None = None,
    ) -> DataObject:
        return CoreDataObject(
            type_, id_=id_, attributes=attributes,
            to_one=to_one, to_many=to_many,
            stub=stub, stub_types=stub_types,
        )

    for ds in data_sources:
        ds.data_object_factory = _factory

    return CoreDataObject
```

Add `CoreDataObject` to `src/tol/core/__init__.py` exports:

```python
from .factory import core_data_object, CoreDataObject  # noqa F401
```

Add a cleanup fixture to `test/unit/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _clean_datasource_registry():
    from tol.core.factory import _data_source_registry
    original = dict(_data_source_registry)
    yield
    _data_source_registry.clear()
    _data_source_registry.update(original)
```

Files that need changes:

| File | Change |
|---|---|
| `src/tol/core/factory.py` | Extract `CoreDataObject` to module level, add `_data_source_registry` |
| `src/tol/core/__init__.py` | Export `CoreDataObject` |
| `test/unit/conftest.py` | Add registry cleanup fixture |

No changes needed to any source files, DataSource implementations, or integration tests — they all go through `core_data_object()` which keeps the same API.

### Benefits

- **Single stable type** — `isinstance` works across DataSource boundaries
- **Importable** — `from tol.core import CoreDataObject` for type hints
- **Inspectable** — `_data_source_registry` can be examined to see what's registered
- **Explicit state** — no hidden closure captures
- **No misleading `ABC`** — the class is concrete
- **Additive registration** — multiple `core_data_object()` calls add to the same registry

### Testing impact

All existing tests pass without changes because `core_data_object()` keeps the same signature and return behaviour:

```python
# test/unit/core/test_factory.py — all still pass
result = core_data_object(_MockDataSource1({}))
assert issubclass(result, DataObject)  # CoreDataObject is returned

ds = _MockDataSource1({})
core_data_object(ds)
assert ds.data_object_factory is not None  # factory still injected

cdo = core_data_object(_MockDataSource1({}), _RelationalDataSource())
data_object = cdo('non-relational')  # cdo is CoreDataObject, callable
```

The `conftest.py` line `mock_ds.data_object_factory = mdo` becomes optional — `core_data_object()` now sets a factory that produces the same `CoreDataObject` type. The line still works if kept.

### Testability improvement

- Registry can be directly manipulated for test setup instead of constructing DataSource subclasses
- `CoreDataObject` can be imported and used in type hints
- `isinstance` checks work reliably across test fixtures
- Tests can inspect `_data_source_registry` to verify registration

### How to write the tests

```python
# test/unit/core/test_factory.py — add to existing file
from tol.core.factory import CoreDataObject, _data_source_registry


class TestCoreDataObjectDI:
    def test_isinstance_across_sources(self):
        """Objects from different core_data_object calls share the same type."""
        ds1 = _MockDataSource1({})
        ds2 = _RelationalDataSource()
        core_data_object(ds1)
        core_data_object(ds2)

        obj1 = CoreDataObject('non-relational', id_='1')
        obj2 = CoreDataObject('a', id_='2')
        assert isinstance(obj1, CoreDataObject)
        assert isinstance(obj2, CoreDataObject)
        assert type(obj1) is type(obj2)

    def test_registry_contains_registered_types(self):
        """Registered DataSource types appear in the registry."""
        ds = _MockDataSource1({})
        core_data_object(ds)
        assert 'non-relational' in _data_source_registry
        assert _data_source_registry['non-relational'] is ds

    def test_registry_additive(self):
        """Multiple core_data_object calls accumulate types."""
        ds1 = _MockDataSource1({})
        ds2 = _RelationalDataSource()
        core_data_object(ds1)
        core_data_object(ds2)
        assert 'non-relational' in _data_source_registry
        assert 'a' in _data_source_registry

    def test_importable_type(self):
        """CoreDataObject can be imported and used as a type hint."""
        ds = _MockDataSource1({})
        core_data_object(ds)
        obj = CoreDataObject('non-relational', id_='1')

        def accepts(o: CoreDataObject) -> str:
            return o.type

        assert accepts(obj) == 'non-relational'

    def test_host_resolved_from_registry(self):
        """_host property reads from the module-level registry."""
        ds = _RelationalDataSource(b_id='b1')
        core_data_object(ds)
        obj = CoreDataObject('a', id_='1')
        assert obj._host is ds


class TestRegistryCleanup:
    """Verifies the autouse fixture isolates tests."""

    def test_empty_registry_raises_on_host(self):
        """Without registration, accessing _host raises KeyError."""
        _data_source_registry.clear()
        obj = CoreDataObject.__new__(CoreDataObject)
        object.__setattr__(obj, '_CoreDataObject__type', 'nonexistent')
        object.__setattr__(obj, '_CoreDataObject__stub_value', False)
        with pytest.raises(KeyError):
            obj._host

    def test_direct_registry_injection(self):
        """DataSources can be injected into the registry directly for testing."""
        from unittest.mock import Mock
        mock_ds = Mock()
        _data_source_registry['test_type'] = mock_ds
        assert _data_source_registry['test_type'] is mock_ds
```

Test isolation fixture for `test/unit/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _clean_datasource_registry():
    """
    Snapshot and restore the DataSource registry between tests.
    Prevents test pollution from core_data_object() calls.
    """
    from tol.core.factory import _data_source_registry
    original = dict(_data_source_registry)
    yield
    _data_source_registry.clear()
    _data_source_registry.update(original)
```
