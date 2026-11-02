<!--
SPDX-FileCopyrightText: 2022 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# ToL SDK

A Python SDK for ToL services. Full documentation is available:
https://tol.pages.internal.sanger.ac.uk/platforms/tol-sdk/
https://ssg-confluence.internal.sanger.ac.uk/display/TOL/ToL+SDK

## Nested Elasticsearch runtime fields

Field arguments to `date_interval`, `latest_date`, `math`, `coalesce`, and
`substring` can be attribute names or nested `RuntimeField` instances:

```python
from tol.core import RuntimeField
from tol.elastic import ElasticRuntimeFields

elapsed = RuntimeField(
    type_='long',
    function='date_interval',
    function_kwargs={
        'start_date': 'created_at',
        'end_date': RuntimeField(
            type_='date',
            function='latest_date',
            function_kwargs={'date_fields': ['updated_at', 'reviewed_at']},
        ),
    },
)

definition = ElasticRuntimeFields.convert_to_request(elapsed)
```

The result is a single runtime-field definition. Nested functions are compiled
into private Painless helpers, not additional named Elasticsearch runtime fields.
Parameters and local variables are scoped so sibling and deeper functions do not
overwrite each other.

- A child that produces no values is missing. `latest_date(allow_missing=False)`
  requires every input; `coalesce` evaluates fallback children only when needed.
- `coalesce` preserves all values from the first nonempty input. Scalar functions
  use the first value, as they do with indexed fields.
- Dates stay as date objects between helpers and become epoch milliseconds only
  when emitted by the outer script. Numeric children respect their declared
  `long` or `double` type.
- The `.keyword` suffix used by `coalesce` and `substring` applies to indexed
  attribute names, not nested keyword results.
- Nested raw scripts and type-only definitions are rejected with `ValueError`.
  Top-level raw scripts and type-only definitions remain supported. Cycles and
  incompatible nested types are also rejected.
