# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Iterable, TypedDict

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    ErrorObject,
)


class BenchlingLoadErrorResult(TypedDict):
    object_type: str
    object_id: str | None
    error_id: str | None
    details: dict[str, Any]
    http_code: int | None


def error_to_result(error: ErrorObject) -> BenchlingLoadErrorResult:
    """Serialize a loader ErrorObject into STS-friendly error details."""
    return {
        'object_type': error.object_type,
        'object_id': error.object_id,
        'error_id': error.error_id,
        'details': error.details,
        'http_code': error.http_code,
    }


def error_sts_sample_id(error: ErrorObject) -> str:
    """Resolve the STS sample id associated with a loader error."""
    if error.object_ is not None and error.object_.id is not None:
        return str(error.object_.id)
    if error.object_id is not None:
        return str(error.object_id)
    raise RuntimeError(f'Unable to resolve STS sample ID for error: {error}')


class CasmBenchlingErrorToStsSampleConverter(DataObjectToDataObjectOrUpdateConverter):
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        """Initialize the converter used to write Benchling load errors to STS."""
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """Convert a Benchling load result or error into an STS sample update."""
        if isinstance(data_object, ErrorObject):
            sample_id = error_sts_sample_id(data_object)
            yield self._data_object_factory(
                'sample',
                str(sample_id),
                attributes={
                    'ep_exported': False,
                    'eln_error': {
                        **error_to_result(data_object),
                        'loader': data_object.details.get('loader'),
                    }
                }
            )
            return

        sample_id = data_object.id
        yield self._data_object_factory(
            'sample',
            str(sample_id),
            attributes={
                'ep_exported': False,
                'eln_error': data_object.attributes.get('eln_error')
            }
        )


class StsSampleUpdateConverter(DataObjectToDataObjectOrUpdateConverter):
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        """Initialize the passthrough STS sample update converter."""
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """Convert a sample data object into an STS sample update."""
        yield self._data_object_factory(
            'sample',
            str(data_object.id),
            attributes=dict(data_object.attributes)
        )
