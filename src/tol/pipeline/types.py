# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable, Protocol

from pydantic import BaseModel

from ..core import (
    DataObject,
    DataObjectFactory,
    DataObjectToDataObjectOrUpdateConverter,
    ErrorObject,
    OperableDataSource,
    Validator,
)


OutStream = Iterable[DataObject | ErrorObject]
"""An outgoing stream of objects. May have failed conversion."""


Step = DataObjectToDataObjectOrUpdateConverter | Validator
"""An arbitrary step in the pipeline."""


class DataSourceConfig(BaseModel):
    module: str
    factory: str

    object_type: str | None = None
    kwargs: dict[str, Any] = {}
    """
    If `None`, on destination, an arbitrarily-typed upsert will occur
    """


class StepConfig(BaseModel):
    module: str
    class_name: str

    # kwargs: dict[str, Any] = {}
    config_details: dict[str, Any] = {}

    # set only for instantiating `Validator`
    is_validator: bool = False
    is_error: bool = True


class PipelineConfig(BaseModel):
    source: DataSourceConfig

    destination: DataSourceConfig | None = None


Pipeline = dict[
    str,  # the name of the step
    Step,
]
"""
The entire pipeline, with named steps.

N.B. `dict` since python 3.7 preserves order.
"""


class DataSourceFactory(Protocol):
    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> OperableDataSource:
        ...


class ConverterFactory(Protocol):
    def __call__(
        self,
        data_object_factory: DataObjectFactory,
        *args: Any
    ) -> DataObjectToDataObjectOrUpdateConverter:
        ...


class ValidatorFactory(Protocol):
    def __call__(self, *args: Any, is_error: bool = False) -> Validator:
        ...
