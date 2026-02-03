# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

class _ElasticDSDict:
    """
    A dictionary mapping object types to datasources,
    with checking to ensure types are supported.
    Used in the Parser, where it is typed simply as a dict.
    """
    pass


class _ConverterFactory:
    """
    Manages the instantiation of `ElasticApiConverter`
    """
    pass


class _FilterFactory:
    """
    Manages the instantiation of `ElasticFilterConverter`
    """
    pass


def _get_client_factory():
    """
    A resonable default for creating
    an `ElasticApiClient` instance
    """
    pass


def create_elastic_datasource():
    """
    Properly instaniates an ElasticDataSource
    using the configuration required for the client
    """
    pass
