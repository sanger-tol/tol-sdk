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

## 2. Error Handling Strategy for DataSource Operations

**Pattern type:** Behavioural (Strategy)

### Current pattern

Error handling across DataSource operations is ad-hoc and inconsistent. Three different approaches are used depending on where the error occurs:

**Actions** (`src/tol/actions/upsert_action.py`, `src/tol/actions/set_status_action.py`) use bare `except Exception` to catch everything and return error dicts:

```python
# src/tol/actions/upsert_action.py
class UpsertAction(Action):
    def run(self, datasource, ids, object_type, params=None):
        data_objects = self.__convert_to_data_objects(...)
        try:
            datasource.upsert_batch(object_type=object_type, objects=data_objects)
            return {'success': True}, 200
        except Exception as e:
            return {'error': str(e)}, 500
```

```python
# src/tol/actions/set_status_action.py
class SetStatusAction(Action):
    def run(self, datasource, ids, object_type, params=None):
        # ...validation...
        try:
            # ...build objects, insert, update parent...
            return {'success': True}, 200
        except Exception as e:  # noqa: BLE001
            return {'error': str(e)}, 500
```

**HTTP transport** (`src/tol/core/http_client.py`) uses `urllib3.Retry` at the session level for a fixed set of status codes:

```python
# src/tol/core/http_client.py
def _get_session_with_retries(self) -> requests.Session:
    retry_strategy = Retry(
        total=self.__retries,          # default 5
        backoff_factor=1,
        status_forcelist=[429, 502, 503, 504]
    )
```

**DataSource subclasses** each implement their own error recovery. For example, `BenchlingDataSource` has a custom method that retries failed bulk upserts by falling back to individual calls.

Two parallel exception hierarchies exist:

| Hierarchy | Location | Exceptions |
|---|---|---|
| `DataSourceError` | `src/tol/core/datasource_error.py` | `UnknownObjectTypeException`, `NoDataObjectFactoryError`, `NotRelationalError` |
| `BaseRuntimeException` | `src/tol/api_client/exception.py` | `ObjectNotFoundByIdException`, `UnsupportedOperationError`, `BadQueryArgError` |

Problems:

1. **Bare `except Exception`** — swallows all errors including `KeyboardInterrupt`-adjacent bugs, makes debugging difficult, and returns a lossy string representation
2. **No error classification** — transient errors (network timeout, 503) and permanent errors (missing field, unknown type) are handled identically
3. **No composable error recovery** — each Action/DataSource reimplements its own try/except; there is no way to share or swap recovery strategies
4. **Two exception hierarchies** — `DataSourceError` and `BaseRuntimeException` are unrelated, so callers cannot catch "any SDK error" without catching `Exception`
5. **Error context is lost** — `str(e)` discards the exception type, traceback, and any structured fields like `status_code`

### Changes required

**Step 1** — Unify the exception hierarchy under `DataSourceError`:

```python
# src/tol/core/datasource_error.py — add classification
from enum import Enum, auto


class ErrorKind(Enum):
    """Classifies errors as transient (retryable) or permanent."""
    TRANSIENT = auto()  # Network timeout, 429, 502, 503, 504
    PERMANENT = auto()  # Missing field, unknown type, auth failure


class DataSourceError(Exception):
    def __init__(self, title: str = None, detail: str = None,
                 status_code: int = 500,
                 kind: ErrorKind = ErrorKind.PERMANENT,
                 cause: Exception | None = None):
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.kind = kind
        self.__cause__ = cause

    @property
    def is_transient(self) -> bool:
        return self.kind == ErrorKind.TRANSIENT

    def __str__(self) -> str:
        return f'{self.title} - "{self.detail}"'


class TransientError(DataSourceError):
    """A retryable error — network issues, rate limits, temporary unavailability."""
    def __init__(self, title: str = None, detail: str = None,
                 status_code: int = 503, cause: Exception | None = None):
        super().__init__(title, detail, status_code,
                         kind=ErrorKind.TRANSIENT, cause=cause)


class PermanentError(DataSourceError):
    """A non-retryable error — bad input, missing config, unknown types."""
    def __init__(self, title: str = None, detail: str = None,
                 status_code: int = 400, cause: Exception | None = None):
        super().__init__(title, detail, status_code,
                         kind=ErrorKind.PERMANENT, cause=cause)
```

**Step 2** — Define an `ErrorHandler` strategy interface:

```python
# src/tol/core/error_handler.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .datasource_error import DataSourceError


class ErrorHandler(ABC):
    """Strategy interface for handling DataSource operation errors."""

    @abstractmethod
    def handle(
        self,
        error: DataSourceError,
        context: dict[str, Any]
    ) -> tuple[dict[str, Any], int]:
        """Handle an error and return a response tuple (body, status_code)."""


class DefaultErrorHandler(ErrorHandler):
    """Preserves current behaviour: return error dict with 500."""

    def handle(self, error, context):
        return {'error': str(error)}, error.status_code


class ClassifyingErrorHandler(ErrorHandler):
    """
    Routes errors based on their ErrorKind.
    Delegates to separate handlers for transient vs permanent errors.
    """

    def __init__(
        self,
        transient_handler: ErrorHandler,
        permanent_handler: ErrorHandler
    ):
        self._transient = transient_handler
        self._permanent = permanent_handler

    def handle(self, error, context):
        if error.is_transient:
            return self._transient.handle(error, context)
        return self._permanent.handle(error, context)


class RetryErrorHandler(ErrorHandler):
    """
    Retries the failed operation up to max_retries times before delegating
    to a fallback handler.
    """

    def __init__(
        self,
        max_retries: int = 3,
        fallback: ErrorHandler | None = None
    ):
        self._max_retries = max_retries
        self._fallback = fallback or DefaultErrorHandler()

    def handle(self, error, context):
        operation = context.get('operation')
        if operation is None:
            return self._fallback.handle(error, context)

        for attempt in range(self._max_retries):
            try:
                result = operation()
                return {'success': True}, 200
            except DataSourceError as retry_error:
                if not retry_error.is_transient:
                    return self._fallback.handle(retry_error, context)
                error = retry_error

        return self._fallback.handle(error, context)


class LoggingErrorHandler(ErrorHandler):
    """
    Wraps another handler, logging the error before delegating.
    Decorator pattern applied to the Strategy.
    """

    def __init__(self, delegate: ErrorHandler, logger=None):
        self._delegate = delegate
        self._logger = logger

    def handle(self, error, context):
        if self._logger:
            self._logger.error(
                'DataSource error in %s: %s (kind=%s, status=%d)',
                context.get('action', 'unknown'),
                error,
                error.kind.name,
                error.status_code
            )
        return self._delegate.handle(error, context)
```

**Step 3** — Inject `ErrorHandler` into `Action`:

```python
# src/tol/actions/action.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..core import DataSource
from ..core.error_handler import DefaultErrorHandler, ErrorHandler


class Action(ABC):
    def __init__(self, error_handler: ErrorHandler | None = None):
        self._error_handler = error_handler or DefaultErrorHandler()

    @abstractmethod
    def _execute(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any], int]:
        """Subclasses implement the operation logic here."""

    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any], int]:
        """Template method: execute the action, delegate errors to the handler."""
        try:
            return self._execute(datasource, ids, object_type, params)
        except DataSourceError as e:
            return self._error_handler.handle(e, {
                'action': type(self).__name__,
                'ids': ids,
                'object_type': object_type,
            })
```

**Step 4** — Update Action subclasses to use `_execute` instead of `run`:

```python
# src/tol/actions/upsert_action.py
class UpsertAction(Action):
    def _execute(self, datasource, ids, object_type, params=None):
        data_objects = self.__convert_to_data_objects(
            datasource=datasource, ids=ids,
            object_type=object_type, params=params
        )
        datasource.upsert_batch(object_type=object_type, objects=data_objects)
        return {'success': True}, 200
```

```python
# src/tol/actions/set_status_action.py
class SetStatusAction(Action):
    def _execute(self, datasource, ids, object_type, params=None):
        # ...validation (raises PermanentError)...
        # ...build objects, insert, update parent...
        return {'success': True}, 200
```

**Step 5** — Update `SetStatusAction` validation to use typed errors:

```python
# src/tol/actions/set_status_action.py
from ..core.datasource_error import PermanentError

class SetStatusAction(Action):
    def _execute(self, datasource, ids, object_type, params=None):
        if not params or 'status' not in params:
            raise PermanentError(
                'Missing status',
                'Missing status from params',
                status_code=400
            )
        if ids is None or len(ids) == 0:
            raise PermanentError(
                'Missing ids',
                'Missing required param: "ids"',
                status_code=400
            )
        # ...rest of logic without try/except...
```

Usage:

```python
# Before — bare except, no configurability
action = UpsertAction()
result, status = action.run(ds, ids=['1'], object_type='sample')
# On error: always returns {'error': '<str>'}, 500

# After — default behaviour unchanged
action = UpsertAction()
result, status = action.run(ds, ids=['1'], object_type='sample')
# On error: returns {'error': '<str>'}, <actual_status_code>

# After — with retry strategy for transient errors
from tol.core.error_handler import (
    ClassifyingErrorHandler, RetryErrorHandler, DefaultErrorHandler
)
handler = ClassifyingErrorHandler(
    transient_handler=RetryErrorHandler(max_retries=3),
    permanent_handler=DefaultErrorHandler()
)
action = UpsertAction(error_handler=handler)
result, status = action.run(ds, ids=['1'], object_type='sample')
# Transient errors retry 3 times; permanent errors fail immediately

# After — with logging
from tol.core.error_handler import LoggingErrorHandler
import logging
logger = logging.getLogger('tol.actions')
handler = LoggingErrorHandler(DefaultErrorHandler(), logger=logger)
action = SetStatusAction(error_handler=handler)
```

Files that need changes:

| File | Change |
|---|---|
| `src/tol/core/datasource_error.py` | Add `ErrorKind`, `TransientError`, `PermanentError`, and `kind`/`cause` fields to `DataSourceError` |
| `src/tol/core/error_handler.py` | New file — `ErrorHandler` ABC with `DefaultErrorHandler`, `ClassifyingErrorHandler`, `RetryErrorHandler`, `LoggingErrorHandler` |
| `src/tol/core/__init__.py` | Export `ErrorHandler`, `ErrorKind` |
| `src/tol/actions/action.py` | Accept `ErrorHandler` in constructor, move `run` to template method calling `_execute` |
| `src/tol/actions/upsert_action.py` | Rename `run` → `_execute`, remove try/except |
| `src/tol/actions/set_status_action.py` | Rename `run` → `_execute`, remove try/except, use `PermanentError` for validation |
| `src/tol/api_client/exception.py` | Make `BaseRuntimeException` extend `DataSourceError` instead of `Exception` |

### Benefits

- Eliminates bare `except Exception` — errors are classified and only `DataSourceError` subtypes are caught
- Error handling is **injectable** — callers choose retry, logging, or custom strategies without modifying Action code
- **Transient vs permanent** classification enables intelligent retry at the application level, not just HTTP transport
- Exception hierarchy is unified — `BaseRuntimeException` becomes a `DataSourceError` subclass, enabling a single catch-all
- Error context is preserved — `cause` chains the original exception, `status_code` flows through to the response
- `Action.run()` becomes a clean Template Method — subclasses implement `_execute` with no error handling boilerplate

### Testing impact

Existing tests that check `action.run()` return values continue to work because `DefaultErrorHandler` preserves the `({'error': str(e)}, status_code)` response format. Tests that directly call `set_status_action.run()` and check for `DataSourceError` raises will need minor updates to expect `PermanentError` instead, though `PermanentError` is a subclass of `DataSourceError` so `pytest.raises(DataSourceError)` still catches it.

### Testability improvement

- Error handlers are independently testable — each strategy can be unit tested without a real DataSource or Action
- Actions can be tested with a `MockErrorHandler` to verify that errors are delegated correctly
- Transient/permanent classification can be asserted directly via `error.is_transient`
- Retry behaviour is testable without network calls — inject a mock operation that fails N times then succeeds
- Error context dict is inspectable — tests can verify what metadata is passed to the handler

### How to write the tests

```python
# test/unit/core/test_error_handler.py
import pytest
from unittest.mock import MagicMock, patch
from tol.core.datasource_error import (
    DataSourceError, ErrorKind, TransientError, PermanentError
)
from tol.core.error_handler import (
    DefaultErrorHandler, ClassifyingErrorHandler,
    RetryErrorHandler, LoggingErrorHandler
)


class TestDefaultErrorHandler:
    def test_returns_error_dict_with_status_code(self):
        handler = DefaultErrorHandler()
        error = DataSourceError('title', 'detail', status_code=404)
        body, status = handler.handle(error, {})
        assert body == {'error': 'title - "detail"'}
        assert status == 404

    def test_handles_transient_and_permanent_equally(self):
        handler = DefaultErrorHandler()
        transient = TransientError('timeout', 'timed out')
        permanent = PermanentError('bad input', 'field missing')
        _, t_status = handler.handle(transient, {})
        _, p_status = handler.handle(permanent, {})
        assert t_status == 503
        assert p_status == 400


class TestClassifyingErrorHandler:
    def test_routes_transient_to_transient_handler(self):
        transient_handler = MagicMock(spec=DefaultErrorHandler)
        transient_handler.handle.return_value = ({'retried': True}, 200)
        permanent_handler = MagicMock(spec=DefaultErrorHandler)
        handler = ClassifyingErrorHandler(transient_handler, permanent_handler)

        error = TransientError('timeout', 'timed out')
        body, status = handler.handle(error, {})

        transient_handler.handle.assert_called_once()
        permanent_handler.handle.assert_not_called()
        assert body == {'retried': True}

    def test_routes_permanent_to_permanent_handler(self):
        transient_handler = MagicMock(spec=DefaultErrorHandler)
        permanent_handler = MagicMock(spec=DefaultErrorHandler)
        permanent_handler.handle.return_value = ({'error': 'bad'}, 400)
        handler = ClassifyingErrorHandler(transient_handler, permanent_handler)

        error = PermanentError('bad input', 'missing field')
        body, status = handler.handle(error, {})

        permanent_handler.handle.assert_called_once()
        transient_handler.handle.assert_not_called()
        assert status == 400


class TestRetryErrorHandler:
    def test_retries_transient_errors(self):
        call_count = 0
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError('fail', f'attempt {call_count}')
            return True

        handler = RetryErrorHandler(max_retries=3)
        error = TransientError('fail', 'attempt 0')
        body, status = handler.handle(error, {'operation': operation})

        assert body == {'success': True}
        assert status == 200
        assert call_count == 3

    def test_gives_up_after_max_retries(self):
        def operation():
            raise TransientError('fail', 'always fails')

        handler = RetryErrorHandler(max_retries=2)
        error = TransientError('fail', 'initial')
        body, status = handler.handle(error, {'operation': operation})

        assert 'error' in body
        assert status == 503

    def test_permanent_error_during_retry_stops_immediately(self):
        call_count = 0
        def operation():
            nonlocal call_count
            call_count += 1
            raise PermanentError('bad', 'not retryable')

        handler = RetryErrorHandler(max_retries=5)
        error = TransientError('fail', 'initial')
        body, status = handler.handle(error, {'operation': operation})

        assert call_count == 1  # Stopped after first permanent error
        assert status == 400

    def test_no_operation_in_context_delegates_to_fallback(self):
        fallback = MagicMock(spec=DefaultErrorHandler)
        fallback.handle.return_value = ({'error': 'no op'}, 500)
        handler = RetryErrorHandler(max_retries=3, fallback=fallback)

        error = TransientError('fail', 'detail')
        handler.handle(error, {})  # No 'operation' key

        fallback.handle.assert_called_once()


class TestLoggingErrorHandler:
    def test_logs_before_delegating(self):
        logger = MagicMock()
        delegate = MagicMock(spec=DefaultErrorHandler)
        delegate.handle.return_value = ({'error': 'x'}, 500)
        handler = LoggingErrorHandler(delegate, logger=logger)

        error = PermanentError('bad', 'detail')
        handler.handle(error, {'action': 'UpsertAction'})

        logger.error.assert_called_once()
        delegate.handle.assert_called_once()

    def test_returns_delegate_result(self):
        delegate = MagicMock(spec=DefaultErrorHandler)
        delegate.handle.return_value = ({'custom': 'response'}, 422)
        handler = LoggingErrorHandler(delegate)

        error = PermanentError('bad', 'detail')
        body, status = handler.handle(error, {})

        assert body == {'custom': 'response'}
        assert status == 422


# test/unit/core/test_datasource_error.py
class TestErrorKind:
    def test_transient_error_is_transient(self):
        error = TransientError('timeout', 'timed out')
        assert error.is_transient is True
        assert error.kind == ErrorKind.TRANSIENT

    def test_permanent_error_is_not_transient(self):
        error = PermanentError('bad input', 'missing')
        assert error.is_transient is False
        assert error.kind == ErrorKind.PERMANENT

    def test_default_datasource_error_is_permanent(self):
        error = DataSourceError('generic', 'detail')
        assert error.is_transient is False

    def test_cause_chaining(self):
        original = ValueError('original cause')
        error = TransientError('wrapper', 'detail', cause=original)
        assert error.__cause__ is original

    def test_transient_error_inherits_datasource_error(self):
        error = TransientError('x', 'y')
        assert isinstance(error, DataSourceError)

    def test_permanent_error_inherits_datasource_error(self):
        error = PermanentError('x', 'y')
        assert isinstance(error, DataSourceError)


# test/unit/actions/test_upsert_action.py
class TestUpsertActionErrorHandling:
    def test_delegates_error_to_handler(self):
        mock_handler = MagicMock(spec=DefaultErrorHandler)
        mock_handler.handle.return_value = ({'handled': True}, 503)
        action = UpsertAction(error_handler=mock_handler)

        mock_ds = MagicMock()
        mock_ds.upsert_batch.side_effect = TransientError('fail', 'timeout')

        body, status = action.run(mock_ds, ['1'], 'sample')

        mock_handler.handle.assert_called_once()
        assert body == {'handled': True}
        assert status == 503

    def test_default_handler_preserves_existing_behaviour(self):
        action = UpsertAction()  # Uses DefaultErrorHandler
        mock_ds = MagicMock()
        mock_ds.upsert_batch.side_effect = DataSourceError(
            'fail', 'detail', status_code=500
        )

        body, status = action.run(mock_ds, ['1'], 'sample')

        assert 'error' in body
        assert status == 500


# test/unit/actions/test_set_status_action.py
class TestSetStatusActionErrorHandling:
    def test_validation_errors_are_permanent(self):
        handler = MagicMock(spec=DefaultErrorHandler)
        handler.handle.return_value = ({'error': 'bad'}, 400)
        action = SetStatusAction(error_handler=handler)

        body, status = action.run(MagicMock(), ['1'], 'sample', params={})

        error_arg = handler.handle.call_args[0][0]
        assert isinstance(error_arg, PermanentError)
        assert error_arg.status_code == 400

    def test_missing_ids_raises_permanent_error(self):
        handler = MagicMock(spec=DefaultErrorHandler)
        handler.handle.return_value = ({'error': 'no ids'}, 400)
        action = SetStatusAction(error_handler=handler)

        body, status = action.run(
            MagicMock(), [], 'sample',
            params={'status': 'approved', 'user_id': 'u1'}
        )

        error_arg = handler.handle.call_args[0][0]
        assert isinstance(error_arg, PermanentError)
```

### Testing patterns

| Pattern | Category | Where used | Purpose |
|---|---|---|---|
| **Arrange-Act-Assert (AAA)** | Structural | All test methods | Each test creates a handler/error, invokes `handle`, and asserts the response — enforcing a consistent structural layout across the test suite |
| **Test Doubles (Mock/Stub)** | Creational | `TestClassifyingErrorHandler`, `TestRetryErrorHandler`, `TestLoggingErrorHandler`, `TestUpsertActionErrorHandling` | `MagicMock(spec=...)` creates strict test doubles for `ErrorHandler` and `DataSource` to isolate the unit under test |
| **State-based Testing** | Behavioural | `TestRetryErrorHandler.test_retries_transient_errors` | Uses a `call_count` closure to track how many times the operation was retried — verifying runtime behavioural state across retry cycles |
| **Behaviour Verification** | Behavioural | `TestLoggingErrorHandler.test_logs_before_delegating` | Asserts that `logger.error` was called exactly once, verifying side-effect behaviour rather than return values |
| **Negative Testing** | Behavioural | `TestRetryErrorHandler.test_gives_up_after_max_retries`, `TestSetStatusActionErrorHandling.test_missing_ids_raises_permanent_error` | Verifies correct behavioural handling of failure paths — exhausted retries and invalid input |
| **Polymorphism Testing** | Structural | `TestErrorKind.test_transient_error_inherits_datasource_error` | `isinstance` checks verify the exception hierarchy structure, ensuring catch clauses work correctly across subtypes |
| **Backward Compatibility Testing** | Behavioural | `TestUpsertActionErrorHandling.test_default_handler_preserves_existing_behaviour` | Confirms that constructing an Action without an explicit handler produces the same behavioural result as the current codebase |

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
