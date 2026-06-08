# CoreDataObject Dependency Injection — Implementation Report

## 1. Implementation Overview

### Original Architecture

`core_data_object()` in `src/tol/core/factory.py` defined a **new class inside the function body** on every call, capturing the DataSource lookup dictionary via closure:

```python
def core_data_object(*data_sources, ...):
    data_source_dict = data_source_dict_factory(*data_sources)

    class CoreDataObject(DataObject, ABC):     # New class created per call
        def __unstub(self):
            data_source_dict[t].get_one(...)   # Closure reference

        @property
        def _host(self):
            return data_source_dict[self.type]  # Closure reference

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return CoreDataObject
```

Key problems:
- **Each call creates a different type** — `isinstance` fails across DataSource boundaries
- **Closure hides state** — `data_source_dict` cannot be inspected, replaced, or mocked
- **`CoreDataObject` cannot be imported** — it only exists inside the function scope
- **Class inherits `ABC`** but is instantiated directly — misleading
- **No additive registration** — each call creates an isolated scope

### New Architecture

`CoreDataObject` is extracted to **module level** with an explicit `_data_source_registry` dictionary:

```python
# Module-level registry
_data_source_registry: dict[str, DataSource] = {}

class CoreDataObject(DataObject):              # Single stable class
    @property
    def _host(self):
        return _data_source_registry[self.type]  # Explicit registry lookup

def core_data_object(*data_sources, ...):      # Same API
    _data_source_registry.update(ds_dict)      # Additive registration
    for ds in data_sources:
        ds.data_object_factory = factory
    return CoreDataObject                       # Always returns the same class
```

The function `core_data_object()` keeps the **exact same signature and return type** — it just updates a module-level registry instead of creating a new closure.

### Impact on Existing Consumers

**Zero breaking changes.** The function API is identical:

```python
# All existing code continues to work
from tol.core import core_data_object
result = core_data_object(ds1, ds2)
obj = result('my_type', id_='123')

# conftest patterns still work
mdo = core_data_object(mock_ds)
mock_ds.data_object_factory = mdo  # Still valid (now redundant but harmless)
```

Consumers gain new capabilities:

```python
# CoreDataObject is now importable for type hints
from tol.core import CoreDataObject

def process(obj: CoreDataObject) -> str:
    return obj.type

# isinstance works across DataSource boundaries
isinstance(obj_from_ds1, CoreDataObject)  # Always True

# Registry is inspectable
from tol.core.factory import _data_source_registry
print(list(_data_source_registry.keys()))  # See all registered types
```

---

## 2. Code Changes

### New Files

| File | Purpose |
|------|---------|
| `test/unit/core/test_factory_di.py` | Unit tests for the DI improvements: type identity, registry behaviour, cleanup |

### Modified Files

| File | Change |
|------|--------|
| `src/tol/core/factory.py` | Extracted `CoreDataObject` to module level. Added `_data_source_registry` dict. Removed `ABC` inheritance. `core_data_object()` now updates the registry additively. |
| `src/tol/core/__init__.py` | Added `CoreDataObject` to exports |
| `test/unit/conftest.py` | Added `_clean_datasource_registry` autouse fixture to snapshot/restore the registry between tests |

### No Files Removed

The change is purely structural — moving the class from function scope to module scope.

### No Config Changes

No changes to `pyproject.toml`, dependencies, or CI configuration.

---

## 3. Quality Improvements

| Dimension | Before | After | Improvement |
|-----------|--------|-------|-------------|
| **Maintainability** | `CoreDataObject` was a 150+ line class defined inside a function body. Editing it required understanding the closure context. The `data_source_dict` was invisible to IDEs and debuggers. | `CoreDataObject` is a standard module-level class. `_data_source_registry` is an explicit, inspectable dict. IDE navigation, refactoring, and debugging all work normally. | Class is visible to tooling; state is explicit and inspectable. |
| **Scalability** | Each `core_data_object()` call created an isolated scope. Types registered in one call were invisible to others. Multiple DataSources required a single monolithic call. | `core_data_object()` calls are **additive** — each adds to the same registry. DataSources can be registered incrementally across modules without coordination. | Supports modular, incremental DataSource registration. |
| **Testability** | Tests required constructing full DataSource subclasses to set up the closure. `isinstance` checks failed across test boundaries. The factory assigned to `mock_ds` had to be overwritten manually. | `_data_source_registry` can be directly manipulated for test setup. `isinstance` works reliably. An autouse fixture ensures test isolation. `CoreDataObject` can be imported for assertions. | Direct registry manipulation; reliable type identity; automatic cleanup. |
| **Consistency** | `CoreDataObject` inherited `ABC` but was instantiated directly (misleading). Different `core_data_object()` calls produced different classes with the same name (confusing in stack traces). | Single concrete `CoreDataObject` class (no `ABC`). All instances share the same type regardless of registration source. Stack traces and `repr()` are unambiguous. | No misleading abstractions; single consistent type identity. |
