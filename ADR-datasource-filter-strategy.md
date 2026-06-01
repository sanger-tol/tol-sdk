# ADR: Unifying DataSource Filter Conversion

**Status:** Proposed  
**Date:** 2026-05-29  
**Author:** TBD

---

## Context

The SDK provides a universal `DataSourceFilter` dataclass (`src/tol/core/datasource_filter.py`) that represents filtering intent in a backend-agnostic way:

```python
@dataclass
class DataSourceFilter:
    exact: Optional[ExactFilter] = None
    contains: Optional[ContainsFilter] = None
    in_list: Optional[InListFilter] = None
    range: Optional[RangeFilter] = None
    and_: Optional[AndFilter] = None
```

Every `DataSource` implementation that supports filtering (via the `_Filterable` mixin used by `ListGetter`, `PageGetter`, `Counter`, and `Cursor` operators) must convert this universal representation into a source-specific query format before executing a read operation. Three independent conversion mechanisms currently exist:

| DataSource | Converter class | Interface | Output type |
|---|---|---|---|
| API (`api_client`) | `DefaultApiFilter` | `ApiFilter.dumps()` | `str` (JSON) |
| Elasticsearch (`elastic`) | `ElasticFilterConverter` | `DataSourceFilterConverter.convert()` | `dict` (ES bool query) |
| PostgreSQL (`sql`) | `DefaultDatabaseFilter` | `DatabaseFilter.filter()` | `Select` (SQLAlchemy) |

A `DataSourceFilterConverter` ABC was recently added to `src/tol/core/datasource_filter_converter.py`, but only the Elastic converter implements it. The API and SQL converters remain on their own separate hierarchies.

Additionally, a preprocessing step — `_Filterable._preprocess_filter()` — converts relative date strings (e.g. `"2 days ago"`) into `datetime` objects. This lives as a method on the `_Filterable` mixin and requires access to `self.get_attribute_metadata_by_name()`, coupling it directly to a DataSource instance.

---

## Current Issues

1. **Three unrelated class hierarchies** — `ApiFilter`, `ElasticFilterConverter` (extends `DataSourceFilterConverter`), and `DatabaseFilter` share no common interface. It is impossible to write code that works with "a filter converter" generically.

2. **Preprocessing is coupled to DataSource instances** — `_preprocess_filter()` requires `self.get_attribute_metadata_by_name()`, making it impossible to test filter preprocessing in isolation without constructing a full DataSource.

3. **Operator handling is duplicated** — each converter independently handles `eq`, `contains`, `in_list`, `gt`, `gte`, `lt`, `lte`, `exists`. Adding a new operator (e.g. `regex`, `not_in_list`) requires parallel changes in three places.

4. **No composable preprocessing pipeline** — preprocessing (date normalisation) and conversion (to source query) are entangled within each DataSource. There is no way to add a new preprocessing step (e.g. field aliasing, permission-based filter injection) without modifying DataSource internals.

5. **Incompatible return types** — `dumps()` returns `str`, `convert()` returns `dict`, `filter()` returns `Select`. The lack of a generic type parameter prevents a unified interface.

6. **Testing requires full DataSource construction** — filter logic cannot be tested without instantiating a concrete DataSource (with config, connections, metadata), even though the conversion itself is a pure data transformation.

---

## Option 1: Generic FilterStrategy with Composable Preprocessor Pipeline

Introduce a generic `FilterStrategy[T]` ABC parameterised by output type, alongside a separate `FilterPreprocessor` chain that handles preprocessing steps independently. Inject the composed strategy into DataSource constructors.

### Design

```python
# src/tol/core/filter_strategy.py
class FilterStrategy(ABC, Generic[T]):
    @abstractmethod
    def convert(self, object_type: str, object_filters: DataSourceFilter | None = None) -> T | None:
        pass

class FilterPreprocessor(ABC):
    @abstractmethod
    def preprocess(self, object_type: str, object_filters: DataSourceFilter) -> DataSourceFilter:
        pass

class CompositeFilterStrategy(FilterStrategy[T]):
    def __init__(self, delegate: FilterStrategy[T], preprocessors: list[FilterPreprocessor] | None = None):
        self._delegate = delegate
        self._preprocessors = preprocessors or []

    def convert(self, object_type, object_filters=None):
        if object_filters is not None:
            for preprocessor in self._preprocessors:
                object_filters = preprocessor.preprocess(object_type, object_filters)
        return self._delegate.convert(object_type, object_filters)
```

Each DataSource receives an optional `filter_strategy` in its constructor:

```python
class ElasticDataSource(...):
    def __init__(self, ..., filter_strategy: FilterStrategy[dict] | None = None):
        self.__filter_strategy = filter_strategy or CompositeFilterStrategy(
            delegate=ElasticFilterStrategy(self._field_or_keyword),
            preprocessors=[DateNormalisingPreprocessor(self)],
        )
```

Existing classes (`DefaultApiFilter`, `ElasticFilterConverter`, `DefaultDatabaseFilter`) are retained as backward-compatible wrappers that delegate to the new strategy internally.

### Advantages

- **Unified interface** — all filter converters implement `FilterStrategy[T]`, enabling generic code and tooling
- **Composable preprocessing** — new preprocessing steps (permissions, field aliasing, audit logging) can be added as pipeline stages without modifying any DataSource
- **Independently testable** — each `FilterStrategy` and `FilterPreprocessor` is a pure-ish function (`DataSourceFilter` → output) testable without network or database connections
- **Injectable for testing** — DataSources can receive a `NoOpFilterStrategy` in tests to isolate non-filter logic
- **Type-safe** — the generic parameter `T` ensures each DataSource's strategy returns the correct output type at type-check time
- **Backward compatible** — existing wrapper classes remain, so downstream code using `DefaultApiFilter` or `ElasticFilterConverter` directly is unaffected

### Disadvantages

- **Higher abstraction count during migration** — while the strategy classes replace existing converters (`ApiFilter` → `ApiFilterStrategy`, `ElasticFilterConverter` → `ElasticFilterStrategy`, `DatabaseFilter` → `SqlFilterStrategy`), the addition of `FilterPreprocessor`, `CompositeFilterStrategy`, and `AttributeMetadataProvider` introduces new abstractions on top of the replacements. During migration both old wrappers and new types coexist, increasing the surface area contributors must understand
- **Generic type complexity** — `FilterStrategy[T]` with `TypeVar` adds complexity for contributors unfamiliar with Python generics; the type parameter doesn't enforce much at runtime
- **Indirection cost** — a filter now passes through `CompositeFilterStrategy` → `FilterPreprocessor` chain → `FilterStrategy.convert()`, adding call-stack depth that makes debugging slightly harder
- **Partial unification** — `SqlFilterStrategy` wraps `DefaultDatabaseFilter` but SQLAlchemy's `Select` building is fundamentally different from dict/string construction. The "shared interface" is somewhat superficial for the SQL case since it still constructs a `Select` internally with joins and aliases
- **Migration effort** — touching 8 files across three DataSource implementations creates a wide-surface-area change that is difficult to review and risky to merge in one pass

---

## Option 2: Extend DataSourceFilterConverter with Preprocessing Hooks

Instead of introducing a new parallel hierarchy, extend the existing `DataSourceFilterConverter` ABC to become the single interface for all filter converters, and add a Template Method for preprocessing.

### Design

Expand the existing `src/tol/core/datasource_filter_converter.py`:

```python
# src/tol/core/datasource_filter_converter.py
from abc import ABC, abstractmethod
from typing import Any

from .datasource_filter import DataSourceFilter


class DataSourceFilterConverter(ABC):
    """
    Converts a DataSourceFilter to a source-specific query.
    Subclasses implement the target-specific conversion logic.
    """

    def __init__(self, metadata: dict[str, dict[str, Any]] | None = None):
        self._metadata = metadata or {}

    def apply(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None
    ) -> Any:
        """Template method: preprocess then convert."""
        if object_filters is None:
            return self._empty_query()
        preprocessed = self._preprocess(object_type, object_filters)
        return self._convert(object_type, preprocessed)

    def _preprocess(
        self,
        object_type: str,
        object_filters: DataSourceFilter
    ) -> DataSourceFilter:
        """
        Default preprocessing: normalise date strings.
        Subclasses can override to add steps.
        """
        if object_filters.and_ is None:
            return object_filters
        for name, value in object_filters.and_.items():
            metadata = self._metadata.get(object_type, {}).get(name)
            if metadata is None:
                continue
            for op, val in value.items():
                if 'value' in val and metadata.get('python_type') == 'datetime' \
                        and isinstance(val['value'], str):
                    import dateparser
                    object_filters.and_[name][op]['value'] = dateparser.parse(val['value'])
        return object_filters

    @abstractmethod
    def _convert(
        self,
        object_type: str,
        object_filters: DataSourceFilter
    ) -> Any:
        """Subclasses implement source-specific conversion here."""

    @abstractmethod
    def _empty_query(self) -> Any:
        """Return the empty/default query for this source."""
```

Migrate existing converters to subclass it:

```python
# src/tol/api_client/filter.py
class ApiFilterConverter(DataSourceFilterConverter):
    def _convert(self, object_type, object_filters):
        pairs = ((k, getattr(object_filters, k)) for k in self.__KEYS)
        return self.__dict_dumper({k: v for k, v in pairs if v is not None})

    def _empty_query(self):
        return None


# src/tol/elastic/filter.py
class ElasticFilterConverter(DataSourceFilterConverter):
    def __init__(self, field_resolver, metadata=None):
        super().__init__(metadata)
        self._field_resolver = field_resolver

    def _convert(self, object_type, object_filters):
        query = self._empty_query()
        # ... build bool query using self._field_resolver ...
        return query

    def _empty_query(self):
        return {'bool': {'must': [], 'must_not': []}}


# src/tol/sql/filter.py
class SqlFilterConverter(DataSourceFilterConverter):
    def __init__(self, base_model, metadata=None):
        super().__init__(metadata)
        self._base_model = base_model

    def _convert(self, object_type, object_filters):
        db_filter = DefaultDatabaseFilter(object_filters)
        query = db_filter.get_query(self._base_model)
        return db_filter.filter(query)

    def _empty_query(self):
        return select(self._base_model.get_id_column()).distinct()
```

DataSources call `converter.apply(object_type, filters)` instead of the current mixed approaches. Preprocessing is extended by overriding `_preprocess()`:

```python
class PermissionAwareElasticConverter(ElasticFilterConverter):
    def __init__(self, field_resolver, user_id, metadata=None):
        super().__init__(field_resolver, metadata)
        self._user_id = user_id

    def _preprocess(self, object_type, object_filters):
        object_filters = super()._preprocess(object_type, object_filters)
        if object_filters.and_ is None:
            object_filters.and_ = {}
        object_filters.and_['owner'] = {'eq': {'value': self._user_id}}
        return object_filters
```

### Advantages

- **Minimal new types** — reuses the existing `DataSourceFilterConverter` class rather than introducing a parallel hierarchy; only adds the `_preprocess` and `_empty_query` template methods
- **Familiar pattern** — Template Method is simpler to understand than Strategy + Decorator + Pipeline composition; new contributors only need to know "subclass and override"
- **Lower migration risk** — `ElasticFilterConverter` already extends `DataSourceFilterConverter`, so only the API and SQL converters need to be migrated (2 files instead of 8)
- **Single call site** — `converter.apply()` replaces both the preprocessing call and the conversion call, simplifying DataSource code
- **No generic type parameters** — avoids `TypeVar` and `Generic[T]` complexity; return type is `Any`, matching the current loose typing across the codebase

### Disadvantages

- **No composable pipeline** — preprocessing extensions require subclassing. Adding two independent preprocessing steps (e.g. date normalisation AND permission filtering) requires creating a combined subclass or a deep inheritance chain
- **Return type is `Any`** — no compile-time guarantee that an Elastic converter returns `dict` or that a SQL converter returns `Select`; errors only surface at runtime
- **Inheritance over composition** — extending preprocessing requires creating new subclasses rather than assembling pipeline steps. This becomes unwieldy if many combinations of preprocessing are needed
- **Preprocessing still receives metadata as a dict** — while decoupled from `self.get_attribute_metadata_by_name()`, the converter must be constructed with a metadata dict, which the DataSource must still provide
- **`_preprocess` is a single hook** — all preprocessing logic must be packed into one overridable method. There is no ordering guarantee or separation between independent concerns (dates vs permissions vs field aliasing)
- **Not independently injectable** — the converter is created internally by each DataSource; there is no constructor parameter to swap it out in tests without subclassing the DataSource itself

---

## Decision

TBD

---

## Consequences

TBD
