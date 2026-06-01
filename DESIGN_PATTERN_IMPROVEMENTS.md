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

### Testing patterns

| Pattern | Category | Where used | Purpose |
|---|---|---|---|
| **Arrange-Act-Assert (AAA)** | Structural | All test methods | Each test sets up state, performs one action, and asserts one outcome — enforcing a consistent structural layout across the test suite |
| **Test Doubles (Mock)** | Creational | `TestDataSourceRegistry` | `MagicMock` replaces real factory callables to verify invocation without constructing real DataSources |
| **Environment Isolation (monkeypatch)** | Behavioural | `TestEnvVar`, `TestSourceDefinition`, `TestDataSourceRegistry` | `monkeypatch.setenv` injects env vars per-test without leaking state between tests — controlling runtime behaviour without modifying production code |
| **Negative Testing** | Behavioural | `TestDataSourceRegistry.test_create_unknown_source_raises` | `pytest.raises` verifies error paths produce the expected exception — asserting behavioural contracts on invalid input |
| **Unit of Behaviour** | Behavioural | `TestSourceDefinition.test_resolve_composes_args` | Tests the composed result of multiple env vars rather than each step, validating the end-to-end resolve pipeline |

---

## 2. DataSource Filter Strategy

**Pattern type:** Behavioural (Strategy)

### Current pattern

Each DataSource implementation has its own filter converter that translates the universal `DataSourceFilter` dataclass into a source-specific query format. Three independent class hierarchies exist with no shared interface:

**API DataSource** (`src/tol/api_client/filter.py`) — serialises filters to a JSON string:

```python
# src/tol/api_client/filter.py
class ApiFilter(ABC):
    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> Optional[str]:
        """Emit a filter string from a DataSourceFilter instance"""

class DefaultApiFilter(ApiFilter):
    __KEYS = ['exact', 'contains', 'in_list', 'range', 'and_']

    def dumps(self, filter_: DataSourceFilter) -> Optional[str]:
        __dict = self.__to_dict(filter_)
        return self.__dict_dumper(__dict)
```

**Elastic DataSource** (`src/tol/elastic/filter.py`) — builds an Elasticsearch bool query dict:

```python
# src/tol/elastic/filter.py
class ElasticFilterConverter(DataSourceFilterConverter):
    def convert(self, object_type: str, object_filters: DataSourceFilter | None = None) -> dict:
        query = {'bool': {'must': [], 'must_not': []}}
        object_filters = self.__elastic_datasource._preprocess_filter(object_type, object_filters)
        if object_filters is None:
            return query
        if object_filters.and_ is not None:
            for k, v in object_filters.and_.items():
                search_field = self.__elastic_datasource._field_or_keyword(object_type, k)
                for op, constraint in v.items():
                    if op in ['gt', 'gte', 'lt', 'lte']:
                        query['bool'][elastic_section].append({'range': {search_field: {op: value}}})
                    if op in ['eq']:
                        query['bool'][elastic_section].append({'match': {search_field: value}})
                    if op in ['contains']:
                        query['bool'][elastic_section].append({'wildcard': {search_field: ...}})
                    if op in ['in_list']:
                        query['bool'][elastic_section].append({'terms': {search_field: value}})
        return query
```

**SQL DataSource** (`src/tol/sql/filter.py`) — builds SQLAlchemy `Select` expressions:

```python
# src/tol/sql/filter.py
class DatabaseFilter(ABC):
    @abstractmethod
    def filter(self, query: Select) -> Select:
        """Filter the Select object using the given model"""

class DefaultDatabaseFilter(DatabaseFilter):
    def filter(self, query: Select) -> Select:
        query = self.__apply_joins(query, self.__alias_trie, self.__base_model)
        query = self.__filter_top_and_(query)
        query = self.__filter_top_exact(query)
        query = self.__filter_top_contains(query)
        query = self.__filter_top_in_list(query)
        query = self.__filter_top_range(query)
        return query
```

Additionally, `_Filterable._preprocess_filter()` in `src/tol/core/operator/_filterable.py` performs in-place date normalisation, tightly coupled to each DataSource:

```python
# src/tol/core/operator/_filterable.py
class _Filterable(ABC):
    def _preprocess_filter(self, object_type, object_filters):
        if object_filters.and_ is not None:
            for name, value in object_filters.and_.items():
                metadata = self.get_attribute_metadata_by_name(object_type, name)
                if metadata['python_type'] == 'datetime' and isinstance(val['value'], str):
                    object_filters.and_[name][op]['value'] = dateparser.parse(val['value'])
        return object_filters
```

A recently-added `DataSourceFilterConverter` ABC (`src/tol/core/datasource_filter_converter.py`) exists but is only used by Elastic:

```python
# src/tol/core/datasource_filter_converter.py
class DataSourceFilterConverter(ABC):
    @abstractmethod
    def convert(self, object_type: str, object_filters: DataSourceFilter | None = None) -> dict | str:
        pass
```

Problems:

1. **Three unrelated hierarchies** — `ApiFilter`, `ElasticFilterConverter` (extends `DataSourceFilterConverter`), and `DatabaseFilter` share no common interface. Code that works with "a filter converter" cannot be written generically.
2. **Preprocessing is coupled to DataSource instances** — `_preprocess_filter()` lives on `_Filterable` and requires `self.get_attribute_metadata_by_name()`, making it impossible to test filter preprocessing without a full DataSource.
3. **Operator handling is duplicated** — each converter independently handles `eq`, `contains`, `in_list`, `gt`, `gte`, `lt`, `lte`, `exists`. Adding a new operator (e.g. `regex`, `not_in_list`) requires changes in three places.
4. **No composable pipeline** — preprocessing (date normalisation) and conversion (to source query) are entangled. There is no way to add a new preprocessing step (e.g. field aliasing, permission filtering) without modifying the DataSource.
5. **`ApiFilter.dumps()` returns `str`, `ElasticFilterConverter.convert()` returns `dict`, `DatabaseFilter.filter()` returns `Select`** — the return types are incompatible, preventing a shared strategy interface.

### Changes required

**Step 1** — Define a unified `FilterStrategy` interface in `src/tol/core/filter_strategy.py`:

```python
# src/tol/core/filter_strategy.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .datasource_filter import DataSourceFilter

T = TypeVar('T')  # The target query type (str, dict, Select)


class FilterStrategy(ABC, Generic[T]):
    """
    Strategy interface for converting a DataSourceFilter into
    a source-specific query representation.
    """

    @abstractmethod
    def convert(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None
    ) -> T | None:
        """Convert a DataSourceFilter to the target query format."""


class FilterPreprocessor(ABC):
    """
    A single preprocessing step applied to a DataSourceFilter
    before conversion.
    """

    @abstractmethod
    def preprocess(
        self,
        object_type: str,
        object_filters: DataSourceFilter
    ) -> DataSourceFilter:
        """Transform the filter in place and return it."""


class DateNormalisingPreprocessor(FilterPreprocessor):
    """
    Converts relative date strings (e.g. '2 days ago') to absolute
    datetime objects using attribute metadata.
    """

    def __init__(self, metadata_provider: AttributeMetadataProvider):
        self._metadata = metadata_provider

    def preprocess(self, object_type, object_filters):
        if object_filters.and_ is None:
            return object_filters
        for name, value in object_filters.and_.items():
            metadata = self._metadata.get_attribute_metadata_by_name(object_type, name)
            if metadata is None:
                continue
            for op, val in value.items():
                if 'value' in val and metadata['python_type'] == 'datetime' \
                        and isinstance(val['value'], str):
                    import dateparser
                    object_filters.and_[name][op]['value'] = dateparser.parse(val['value'])
        return object_filters


class AttributeMetadataProvider(ABC):
    """Extracts attribute metadata lookup from DataSource coupling."""

    @abstractmethod
    def get_attribute_metadata_by_name(
        self, object_type: str, field_name: str
    ) -> dict[str, Any] | None:
        pass


class CompositeFilterStrategy(FilterStrategy[T]):
    """
    Composes a pipeline of preprocessors with a final conversion strategy.
    Decorator pattern applied to FilterStrategy.
    """

    def __init__(
        self,
        delegate: FilterStrategy[T],
        preprocessors: list[FilterPreprocessor] | None = None,
    ):
        self._delegate = delegate
        self._preprocessors = preprocessors or []

    def convert(self, object_type, object_filters=None):
        if object_filters is not None:
            for preprocessor in self._preprocessors:
                object_filters = preprocessor.preprocess(object_type, object_filters)
        return self._delegate.convert(object_type, object_filters)
```

**Step 2** — Adapt existing converters to implement `FilterStrategy`:

```python
# src/tol/api_client/filter.py
from ..core.filter_strategy import FilterStrategy


class ApiFilterStrategy(FilterStrategy[str]):
    """Adapts the existing ApiFilter to the FilterStrategy interface."""

    __KEYS = ['exact', 'contains', 'in_list', 'range', 'and_']

    def __init__(self, dict_dumper: DictDumper = default_dict_dumper):
        self.__dict_dumper = dict_dumper

    def convert(self, object_type, object_filters=None):
        if object_filters is None:
            return None
        pairs = (
            (k, getattr(object_filters, k))
            for k in self.__KEYS
        )
        __dict = {k: v for k, v in pairs if v is not None}
        return self.__dict_dumper(__dict)
```

```python
# src/tol/elastic/filter.py
from ..core.filter_strategy import FilterStrategy


class ElasticFilterStrategy(FilterStrategy[dict]):
    """Adapts ElasticFilterConverter to the FilterStrategy interface."""

    def __init__(self, field_resolver: Callable[[str, str], str]):
        self._field_resolver = field_resolver

    def convert(self, object_type, object_filters=None):
        query = {'bool': {'must': [], 'must_not': []}}
        if object_filters is None:
            return query
        if object_filters.and_ is not None:
            for k, v in object_filters.and_.items():
                search_field = self._field_resolver(object_type, k)
                for op, constraint in v.items():
                    search_value = constraint.get('value')
                    negated = constraint.get('negate', False)
                    elastic_section = 'must_not' if negated else 'must'
                    if op in ['gt', 'gte', 'lt', 'lte']:
                        query['bool'][elastic_section].append(
                            {'range': {search_field: {op: search_value}}}
                        )
                    if op in ['eq']:
                        query['bool'][elastic_section].append(
                            {'match': {search_field: search_value}}
                        )
                    if op in ['contains']:
                        query['bool'][elastic_section].append(
                            {'wildcard': {search_field: {'value': f'{search_value}*'}}}
                        )
                    if op in ['in_list']:
                        query['bool'][elastic_section].append(
                            {'terms': {search_field: search_value}}
                        )
        return query
```

```python
# src/tol/sql/filter.py
from ..core.filter_strategy import FilterStrategy
from sqlalchemy import Select


class SqlFilterStrategy(FilterStrategy[Select]):
    """Adapts DefaultDatabaseFilter to the FilterStrategy interface."""

    def __init__(self, base_model: type[Model], model_registry: dict[str, type[Model]]):
        self._base_model = base_model
        self._model_registry = model_registry

    def convert(self, object_type, object_filters=None):
        db_filter = DefaultDatabaseFilter(object_filters)
        query = db_filter.get_query(self._base_model)
        return db_filter.filter(query)
```

**Step 3** — Inject `FilterStrategy` into DataSource constructors:

```python
# src/tol/elastic/elastic_datasource.py
class ElasticDataSource(...):
    def __init__(self, ..., filter_strategy: FilterStrategy[dict] | None = None):
        ...
        self.__filter_strategy = filter_strategy or CompositeFilterStrategy(
            delegate=ElasticFilterStrategy(self._field_or_keyword),
            preprocessors=[DateNormalisingPreprocessor(self)],
        )

    def __get_page_response(self, object_type, object_filters, ...):
        query = self.__filter_strategy.convert(object_type, object_filters)
        ...
```

```python
# src/tol/api_client/api_datasource.py
class ApiDataSource(...):
    def __init__(self, ..., filter_strategy: FilterStrategy[str] | None = None):
        ...
        self.__filter_strategy = filter_strategy or CompositeFilterStrategy(
            delegate=ApiFilterStrategy(),
            preprocessors=[DateNormalisingPreprocessor(self)],
        )

    def __get_filter_string(self, object_filters):
        return self.__filter_strategy.convert(None, object_filters)
```

Keep existing classes as backward-compatible wrappers:

```python
# src/tol/api_client/filter.py — keep for backward compat
class DefaultApiFilter(ApiFilter):
    def __init__(self, dict_dumper=default_dict_dumper):
        self.__strategy = ApiFilterStrategy(dict_dumper)

    def dumps(self, filter_: DataSourceFilter) -> Optional[str]:
        return self.__strategy.convert(None, filter_)
```

Usage:

```python
# Before — tightly coupled, no way to customise
ds = ElasticDataSource(config)
# Date preprocessing happens internally, cannot add steps

# After — composable pipeline
from tol.core.filter_strategy import CompositeFilterStrategy, DateNormalisingPreprocessor

# Add a custom preprocessor that restricts queries by permission
class PermissionPreprocessor(FilterPreprocessor):
    def __init__(self, user_id: str, allowed_types: list[str]):
        self._user_id = user_id
        self._allowed_types = allowed_types

    def preprocess(self, object_type, object_filters):
        if object_filters.and_ is None:
            object_filters.and_ = {}
        object_filters.and_['owner'] = {'eq': {'value': self._user_id}}
        return object_filters

strategy = CompositeFilterStrategy(
    delegate=ElasticFilterStrategy(ds._field_or_keyword),
    preprocessors=[
        PermissionPreprocessor(user_id='u123', allowed_types=['sample']),
        DateNormalisingPreprocessor(ds),
    ],
)
ds = ElasticDataSource(config, filter_strategy=strategy)

# Override strategy for testing — no network needed
from tol.core.filter_strategy import FilterStrategy

class NoOpFilterStrategy(FilterStrategy[dict]):
    def convert(self, object_type, object_filters=None):
        return {'bool': {'must': [], 'must_not': []}}

test_ds = ElasticDataSource(config, filter_strategy=NoOpFilterStrategy())
```

Files that need changes:

| File | Change |
|---|---|
| `src/tol/core/filter_strategy.py` | New file — `FilterStrategy[T]` ABC, `FilterPreprocessor` ABC, `DateNormalisingPreprocessor`, `AttributeMetadataProvider`, `CompositeFilterStrategy` |
| `src/tol/core/__init__.py` | Export `FilterStrategy`, `FilterPreprocessor`, `CompositeFilterStrategy` |
| `src/tol/api_client/filter.py` | Add `ApiFilterStrategy(FilterStrategy[str])`, keep `DefaultApiFilter` as wrapper |
| `src/tol/elastic/filter.py` | Add `ElasticFilterStrategy(FilterStrategy[dict])`, keep `ElasticFilterConverter` as wrapper |
| `src/tol/sql/filter.py` | Add `SqlFilterStrategy(FilterStrategy[Select])`, keep `DefaultDatabaseFilter` unchanged |
| `src/tol/elastic/elastic_datasource.py` | Accept optional `filter_strategy` in constructor, use it in query methods |
| `src/tol/api_client/api_datasource.py` | Accept optional `filter_strategy` in constructor, use it in `__get_filter_string` |
| `src/tol/core/operator/_filterable.py` | Extract date logic to `DateNormalisingPreprocessor`, keep `_preprocess_filter` as thin delegate |

### Benefits

- Eliminates three unrelated filter hierarchies — all converters implement `FilterStrategy[T]`
- Preprocessing is **composable** — add permission filtering, field aliasing, or audit logging as pipeline steps without modifying DataSource code
- Filter conversion is **injectable** — swap strategies for testing without constructing real DataSources or network connections
- Adding a new operator only requires implementing it in the relevant `FilterStrategy` — other strategies are unaffected
- `DateNormalisingPreprocessor` is independently testable without a DataSource instance
- The `CompositeFilterStrategy` separates preprocessing from conversion, following the Single Responsibility Principle

### Testing impact

Existing tests that call DataSource methods with `object_filters` continue to work because the default `CompositeFilterStrategy` is wired identically to the current inline behaviour. Tests that directly instantiate `DefaultApiFilter` or `ElasticFilterConverter` are unaffected — these classes remain as wrappers.

### Testability improvement

- `FilterStrategy` implementations are testable in isolation — pass a `DataSourceFilter`, assert the output format without any network or database
- `FilterPreprocessor` steps are independently testable — verify date parsing without constructing an Elastic client
- `CompositeFilterStrategy` can be tested with mock preprocessors to verify pipeline ordering
- DataSource integration tests can inject a `NoOpFilterStrategy` to isolate non-filter logic
- New preprocessors (permissions, audit) can be unit tested without touching existing DataSource tests

### How to write the tests

```python
# test/unit/core/test_filter_strategy.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from tol.core.datasource_filter import DataSourceFilter
from tol.core.filter_strategy import (
    CompositeFilterStrategy,
    DateNormalisingPreprocessor,
    FilterPreprocessor,
    FilterStrategy,
)


class TestFilterStrategy:
    def test_convert_receives_filter_and_returns_target_type(self):
        class StubStrategy(FilterStrategy[dict]):
            def convert(self, object_type, object_filters=None):
                return {'converted': True}

        strategy = StubStrategy()
        result = strategy.convert('sample', DataSourceFilter(exact={'name': 'x'}))
        assert result == {'converted': True}

    def test_convert_with_none_filter(self):
        class StubStrategy(FilterStrategy[str]):
            def convert(self, object_type, object_filters=None):
                return None if object_filters is None else 'has_filter'

        strategy = StubStrategy()
        assert strategy.convert('sample', None) is None
        assert strategy.convert('sample', DataSourceFilter()) == 'has_filter'


class TestFilterPreprocessor:
    def test_preprocess_modifies_filter_in_place(self):
        class AddOwnerPreprocessor(FilterPreprocessor):
            def preprocess(self, object_type, object_filters):
                if object_filters.and_ is None:
                    object_filters.and_ = {}
                object_filters.and_['owner'] = {'eq': {'value': 'user1'}}
                return object_filters

        preprocessor = AddOwnerPreprocessor()
        f = DataSourceFilter(and_={'name': {'eq': {'value': 'test'}}})
        result = preprocessor.preprocess('sample', f)
        assert 'owner' in result.and_
        assert result.and_['name'] == {'eq': {'value': 'test'}}


class TestDateNormalisingPreprocessor:
    def test_converts_relative_date_string_to_datetime(self):
        metadata_provider = MagicMock()
        metadata_provider.get_attribute_metadata_by_name.return_value = {
            'python_type': 'datetime'
        }
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'created_at': {'gt': {'value': '2 days ago'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert isinstance(result.and_['created_at']['gt']['value'], datetime)

    def test_leaves_non_datetime_fields_unchanged(self):
        metadata_provider = MagicMock()
        metadata_provider.get_attribute_metadata_by_name.return_value = {
            'python_type': 'str'
        }
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'test_value'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert result.and_['name']['eq']['value'] == 'test_value'

    def test_handles_none_metadata_gracefully(self):
        metadata_provider = MagicMock()
        metadata_provider.get_attribute_metadata_by_name.return_value = None
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'unknown_field': {'eq': {'value': 'x'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert result.and_['unknown_field']['eq']['value'] == 'x'

    def test_skips_when_and_is_none(self):
        metadata_provider = MagicMock()
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(exact={'name': 'x'})

        result = preprocessor.preprocess('sample', f)

        metadata_provider.get_attribute_metadata_by_name.assert_not_called()
        assert result.exact == {'name': 'x'}


class TestCompositeFilterStrategy:
    def test_applies_preprocessors_before_conversion(self):
        call_order = []

        class TrackingPreprocessor(FilterPreprocessor):
            def __init__(self, label):
                self.label = label

            def preprocess(self, object_type, object_filters):
                call_order.append(f'preprocess_{self.label}')
                return object_filters

        class TrackingStrategy(FilterStrategy[str]):
            def convert(self, object_type, object_filters=None):
                call_order.append('convert')
                return 'result'

        composite = CompositeFilterStrategy(
            delegate=TrackingStrategy(),
            preprocessors=[TrackingPreprocessor('a'), TrackingPreprocessor('b')],
        )
        composite.convert('sample', DataSourceFilter())

        assert call_order == ['preprocess_a', 'preprocess_b', 'convert']

    def test_skips_preprocessing_when_filter_is_none(self):
        preprocessor = MagicMock(spec=FilterPreprocessor)
        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = {'empty': True}

        composite = CompositeFilterStrategy(delegate, preprocessors=[preprocessor])
        result = composite.convert('sample', None)

        preprocessor.preprocess.assert_not_called()
        delegate.convert.assert_called_once_with('sample', None)
        assert result == {'empty': True}

    def test_passes_preprocessed_filter_to_delegate(self):
        class UpperCasePreprocessor(FilterPreprocessor):
            def preprocess(self, object_type, object_filters):
                if object_filters.exact:
                    object_filters.exact = {
                        k: v.upper() if isinstance(v, str) else v
                        for k, v in object_filters.exact.items()
                    }
                return object_filters

        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = 'ok'

        composite = CompositeFilterStrategy(
            delegate, preprocessors=[UpperCasePreprocessor()]
        )
        f = DataSourceFilter(exact={'name': 'hello'})
        composite.convert('sample', f)

        called_filter = delegate.convert.call_args[0][1]
        assert called_filter.exact['name'] == 'HELLO'

    def test_no_preprocessors_delegates_directly(self):
        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = 'direct'

        composite = CompositeFilterStrategy(delegate)
        f = DataSourceFilter(exact={'x': 1})
        result = composite.convert('sample', f)

        assert result == 'direct'
        delegate.convert.assert_called_once_with('sample', f)


# test/unit/api_client/test_api_filter_strategy.py
class TestApiFilterStrategy:
    def test_converts_exact_filter_to_json_string(self):
        from tol.api_client.filter import ApiFilterStrategy
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(exact={'name': 'test'})

        result = strategy.convert('sample', f)

        assert '"exact"' in result
        assert '"name"' in result
        assert '"test"' in result

    def test_returns_none_for_none_filter(self):
        from tol.api_client.filter import ApiFilterStrategy
        strategy = ApiFilterStrategy()
        assert strategy.convert('sample', None) is None

    def test_excludes_none_filter_fields(self):
        from tol.api_client.filter import ApiFilterStrategy
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(exact={'name': 'x'}, contains=None)

        result = strategy.convert('sample', f)

        assert 'contains' not in result


# test/unit/elastic/test_elastic_filter_strategy.py
class TestElasticFilterStrategy:
    def test_converts_eq_to_match_query(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'test'}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'name': 'test'}} in result['bool']['must']

    def test_converts_range_operators(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'age': {'gte': {'value': 18}}
        })
        result = strategy.convert('sample', f)

        assert {'range': {'age': {'gte': 18}}} in result['bool']['must']

    def test_negated_filter_goes_to_must_not(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'status': {'eq': {'value': 'deleted', 'negate': True}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'status': 'deleted'}} in result['bool']['must_not']

    def test_returns_empty_bool_for_none_filter(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        result = strategy.convert('sample', None)

        assert result == {'bool': {'must': [], 'must_not': []}}

    def test_uses_field_resolver_for_field_names(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = MagicMock(return_value='name.keyword')
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'x'}}
        })
        strategy.convert('sample', f)

        resolver.assert_called_with('sample', 'name')

    def test_in_list_creates_terms_query(self):
        from tol.elastic.filter import ElasticFilterStrategy
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'status': {'in_list': {'value': ['active', 'pending']}}
        })
        result = strategy.convert('sample', f)

        assert {'terms': {'status': ['active', 'pending']}} in result['bool']['must']
```

### Testing patterns

| Pattern | Category | Where used | Purpose |
|---|---|---|---|
| **Arrange-Act-Assert (AAA)** | Structural | All test methods | Each test constructs a strategy/filter, invokes `convert` or `preprocess`, and asserts the output — enforcing a consistent structural layout across the test suite |
| **Test Doubles (Mock/Stub)** | Creational | `TestCompositeFilterStrategy`, `TestDateNormalisingPreprocessor`, `TestElasticFilterStrategy` | `MagicMock(spec=...)` creates strict test doubles for `FilterStrategy`, `FilterPreprocessor`, and `AttributeMetadataProvider` to isolate the unit under test |
| **Ordering Verification** | Behavioural | `TestCompositeFilterStrategy.test_applies_preprocessors_before_conversion` | Uses a `call_order` list to track the sequence of method invocations — verifying the pipeline executes preprocessors before the final conversion |
| **Polymorphism Testing** | Structural | `TestFilterStrategy.test_convert_receives_filter_and_returns_target_type` | Verifies that concrete implementations of the generic `FilterStrategy[T]` interface return the expected type — confirming the strategy contract is honoured |
| **Negative Testing** | Behavioural | `TestCompositeFilterStrategy.test_skips_preprocessing_when_filter_is_none`, `TestDateNormalisingPreprocessor.test_handles_none_metadata_gracefully` | Verifies correct behavioural handling of null/missing inputs without raising exceptions |
| **State Transformation Testing** | Behavioural | `TestCompositeFilterStrategy.test_passes_preprocessed_filter_to_delegate` | Asserts that the filter object passed to the delegate has been mutated by the preprocessor — verifying the pipeline's data-flow behaviour |
| **Backward Compatibility Testing** | Behavioural | `TestApiFilterStrategy.test_converts_exact_filter_to_json_string` | Confirms that the new strategy produces output identical to the existing `DefaultApiFilter.dumps()` method — preserving current serialisation behaviour |

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

### Testing patterns

| Pattern | Category | Where used | Purpose |
|---|---|---|---|
| **Arrange-Act-Assert (AAA)** | Structural | All test methods | Each test registers DataSources, performs one operation, and asserts one outcome — enforcing a consistent structural layout |
| **Test Doubles (Mock)** | Creational | `TestRegistryCleanup.test_direct_registry_injection` | `Mock()` creates lightweight stand-ins for DataSource objects, enabling test setup without constructing real implementations |
| **Identity Assertion** | Structural | `TestCoreDataObjectDI.test_isinstance_across_sources` | `type(obj1) is type(obj2)` verifies the structural guarantee that a single class exists regardless of registration source |
| **State Isolation (Fixture)** | Behavioural | `TestRegistryCleanup`, `_clean_datasource_registry` fixture | Snapshot-and-restore pattern ensures each test starts with a clean registry — controlling behavioural side-effects of `core_data_object()` calls |
| **Negative Testing** | Behavioural | `TestRegistryCleanup.test_empty_registry_raises_on_host` | `pytest.raises(KeyError)` verifies behavioural contracts when accessing an unregistered type |
| **Integration Verification** | Structural | `TestCoreDataObjectDI.test_host_resolved_from_registry` | `obj._host is ds` verifies the structural wiring between `CoreDataObject` and the registry — confirming DI is correctly plumbed |
