# DataSource Filter Strategy — Implementation Report

## 1. Implementation Overview

### Original Architecture

Filter conversion in the SDK was spread across **three independent class hierarchies** with no shared interface:

| Converter | Location | Input | Output | Interface |
|-----------|----------|-------|--------|-----------|
| `DefaultApiFilter` | `src/tol/api_client/filter.py` | `DataSourceFilter` | JSON string | `ApiFilter.dumps()` |
| `ElasticFilterConverter` | `src/tol/elastic/filter.py` | `DataSourceFilter` | Elasticsearch bool query dict | `DataSourceFilterConverter.convert()` |
| `DefaultDatabaseFilter` | `src/tol/sql/filter.py` | `DataSourceFilter` | SQLAlchemy `Select` | `DatabaseFilter.filter()` |

Additionally, date preprocessing was tightly coupled to DataSource instances via `_Filterable._preprocess_filter()` in `src/tol/core/operator/_filterable.py`, which required `self.get_attribute_metadata_by_name()` — making it impossible to test without a full DataSource.

Key problems:
- No shared interface across the three converters
- Preprocessing entangled with conversion — no composable pipeline
- Adding a new operator required changes in three places
- Filter logic untestable in isolation from DataSource instances

### New Architecture

A unified **FilterStrategy** pattern provides:

```
src/tol/core/filter_strategy.py
├── FilterStrategy[T]              — Generic ABC for all converters
├── FilterPreprocessor             — ABC for pipeline preprocessing steps
├── AttributeMetadataProvider      — Decouples metadata from DataSource
├── DateNormalisingPreprocessor    — Extracted from _Filterable
└── CompositeFilterStrategy[T]     — Composes preprocessors + strategy

src/tol/api_client/filter.py
└── ApiFilterStrategy(FilterStrategy[str])     — New, standalone

src/tol/elastic/filter.py
└── ElasticFilterStrategy(FilterStrategy[dict]) — New, standalone

src/tol/sql/filter.py
└── SqlFilterStrategy(FilterStrategy[Select])   — New, standalone
```

Each DataSource now optionally accepts a `filter_strategy` parameter in its constructor. If provided, it's used instead of the default inline filter path. The default behaviour is preserved identically.

### Impact on Existing Consumers

**Zero breaking changes.** All existing code paths continue to work:

```python
# These all work exactly as before
ds = ElasticDataSource(config, ...)  # No filter_strategy → uses ElasticFilterConverter
ds.get_list('sample', object_filters=f)  # Internally creates ElasticFilterConverter(self)

api_ds = create_api_datasource(...)  # Still uses DefaultApiFilter via factory
```

Consumers gain the ability to **inject custom filter strategies**:

```python
from tol.core.filter_strategy import CompositeFilterStrategy, DateNormalisingPreprocessor
from tol.elastic.filter import ElasticFilterStrategy

# Custom preprocessor
class PermissionPreprocessor(FilterPreprocessor):
    def preprocess(self, object_type, object_filters):
        # Add permission constraints
        return object_filters

# Composable pipeline
strategy = CompositeFilterStrategy(
    delegate=ElasticFilterStrategy(ds._field_or_keyword),
    preprocessors=[PermissionPreprocessor(), DateNormalisingPreprocessor(ds)],
)
ds = ElasticDataSource(config, ..., filter_strategy=strategy)
```

---

## 2. Code Changes

### New Files

| File | Purpose |
|------|---------|
| `src/tol/core/filter_strategy.py` | Core module — `FilterStrategy[T]`, `FilterPreprocessor`, `AttributeMetadataProvider`, `DateNormalisingPreprocessor`, `CompositeFilterStrategy` |
| `test/unit/core/test_filter_strategy.py` | Unit tests for the core strategy, preprocessor, and composite classes |
| `test/unit/api_client/test_api_filter_strategy.py` | Unit tests for `ApiFilterStrategy` |
| `test/unit/elastic/test_elastic_filter_strategy.py` | Unit tests for `ElasticFilterStrategy` |

### Modified Files

| File | Change |
|------|--------|
| `src/tol/core/__init__.py` | Added exports: `FilterStrategy`, `FilterPreprocessor`, `CompositeFilterStrategy`, `AttributeMetadataProvider`, `DateNormalisingPreprocessor` |
| `src/tol/api_client/filter.py` | Added `ApiFilterStrategy(FilterStrategy[str])`. `DefaultApiFilter` now delegates to it internally. |
| `src/tol/elastic/filter.py` | Added `ElasticFilterStrategy(FilterStrategy[dict])`. `ElasticFilterConverter` now delegates to it. Removed duplicate `_build_elasticsearch_query` function. |
| `src/tol/sql/filter.py` | Added `SqlFilterStrategy(FilterStrategy[Select])` that wraps `DefaultDatabaseFilter`. Added import of `FilterStrategy`. |
| `src/tol/elastic/elastic_datasource.py` | Constructor accepts optional `filter_strategy` parameter. `_prepare_get_params` uses it if present. |
| `src/tol/api_client/api_datasource.py` | Constructor accepts optional `filter_strategy` parameter. `__get_filter_string` uses it if present. |
| `src/tol/core/operator/_filterable.py` | Date preprocessing logic extracted to `DateNormalisingPreprocessor`. `_preprocess_filter` now delegates to it via `_DataSourceMetadataAdapter`. |

### No Files Removed

All existing classes (`DefaultApiFilter`, `ElasticFilterConverter`, `DefaultDatabaseFilter`, `DatabaseFilter`, `ApiFilter`) are preserved as backward-compatible wrappers/implementations.

### No Config Changes

No changes to `pyproject.toml`, dependencies, or CI configuration. The only new dependency used is `dateparser`, which was already imported by `_filterable.py`.

---

## 3. Quality Improvements

| Dimension | Before | After | Improvement |
|-----------|--------|-------|-------------|
| **Maintainability** | Three unrelated hierarchies (`ApiFilter`, `DataSourceFilterConverter`, `DatabaseFilter`) with duplicated operator handling. Adding a new operator required changes in 3 files. | All converters implement `FilterStrategy[T]`. Each strategy is self-contained. New operators only need changes in the relevant strategy. | Single interface, single responsibility per strategy. |
| **Scalability** | Adding a new preprocessing step (e.g. permission filtering, field aliasing) required modifying DataSource internals. No way to compose multiple steps. | `CompositeFilterStrategy` composes an arbitrary pipeline of `FilterPreprocessor` steps with a final conversion strategy. New steps are additive — no existing code modified. | O(1) effort to add new preprocessing steps. |
| **Testability** | Filter conversion required a full DataSource instance (with network config, metadata, etc). `_preprocess_filter` required `self.get_attribute_metadata_by_name()`. Zero standalone filter tests existed. | `FilterStrategy` implementations accept only their dependencies (e.g. a `field_resolver` callable). `DateNormalisingPreprocessor` accepts a simple `AttributeMetadataProvider` interface. All testable with mocks. | Full unit test coverage without DataSource instances or network. |
| **Consistency** | `ApiFilter.dumps()` returned `str`, `ElasticFilterConverter.convert()` returned `dict`, `DatabaseFilter.filter()` took and returned `Select`. No shared contract. | All implement `FilterStrategy[T].convert(object_type, object_filters) → T`. Generic type parameter makes the output type explicit. | Uniform interface across all filter backends. |
