# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, PropertyMock

from tol.core import DataSource
from tol.log import (
    Logger,
    UserIdGetter,
    elastic_logger
)


class TestElasticLogger:
    """Tests the `elastic_logger` factory function"""

    def test_arguments(self):
        """Tests arguments are passed in correctly"""

        mock_ds_class = Mock()
        mock_ds = Mock()
        mock_ds_class.return_value = mock_ds

        mock_logger = Mock()

        def __logger_factory(
            ds: DataSource,
            app_name: str,
            _
        ) -> Logger:

            assert ds == mock_ds
            assert app_name == 'my-app'

            return mock_logger

        observed_logger = elastic_logger(
            'a fun URI that is really great',
            'me',
            'please',
            'my-app',
            elastic_factory=lambda c: mock_ds_class(c),
            logger_factory=__logger_factory
        )
        assert observed_logger == mock_logger

        expected_config = {
            'uri': 'a fun URI that is really great',
            'user': 'me',
            'password': 'please',
            'index_prefix': '',
            'relationship_cfg': {}
        }
        mock_ds_class.assert_called_once_with(
            expected_config
        )

    def test_data_object_factory(self):
        """
        The `ElasticDataSource().data_object_factory` has a non-`None`
        value, and can hence create `DataObject` instances.
        """

        mock_ds_class = Mock()
        type(mock_ds_class).data_object_factory = PropertyMock()
        elastic_logger(
            'a fun URI that is really great',
            'me',
            'please',
            'my-app',
            elastic_factory=lambda c: mock_ds_class(c)
        )
        type(mock_ds_class).data_object_factory.setter.assert_called_once()
