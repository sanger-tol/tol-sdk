# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Callable, Iterator, Optional

from .converter import (
    S3Converter
)
from .parser import DefaultParser
from .s3_datasource import (
    S3ConverterFactory,
    S3DataSource
)
from ..core import DataSource
from ..services.s3_client import S3Client


class _S3DSDict(Mapping):
    def __init__(self, s3_ds: S3DataSource) -> None:
        self.__ds = s3_ds

    def __getitem__(self, __k: str) -> S3DataSource:
        if __k not in self.__ds.supported_types:
            raise KeyError()
        return self.__ds

    def __iter__(self) -> Iterator[str]:
        return iter(self.__ds.supported_types)

    def __len__(self) -> int:
        return len(self.__ds.supported_types)


class _ConverterFactory:
    """
    Manages the instantation of:

    - `S3Converter`
    """

    def __init__(self) -> None:
        self.__data_source: Optional[DataSource] = None

    @property
    def data_source(self) -> Optional[DataSource]:
        return self.__data_source

    @data_source.setter
    def data_source(
        self,
        ds: DataSource
    ) -> None:

        self.__data_source = ds

    def s3_converter_factory(self) -> S3ConverterFactory:
        """
        Returns an instantiated `S3Converter`.
        """

        parser = DefaultParser(self.__ds_dict)
        return S3Converter(parser)

    @property
    def __ds_dict(self) -> dict[str, DataSource]:
        return _S3DSDict(self.data_source)


def _get_client_factory() -> Callable[[], S3Client]:
    """
    A resonable default for creating
    an `S3Client` instance
    """

    return lambda: S3Client()


def create_s3_datasource(
    bucket_name: str,
    prefix: str = None
) -> S3DataSource:
    """
    Instantiates `S3DataSource` using the given:

    - `bucket_name`
    """

    client_factory = _get_client_factory()
    manager = _ConverterFactory()
    s3_ds = S3DataSource(
        client_factory,
        manager.s3_converter_factory,
        bucket_name,
        prefix
    )

    manager.data_source = s3_ds

    return s3_ds
