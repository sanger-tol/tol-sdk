# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

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
        mock_user_id_getter = Mock()

        def __logger_factory(
            ds: DataSource,
            app_name: str,
            user_id_getter: UserIdGetter
        ) -> Logger:

            assert ds == mock_ds
            assert app_name == 'my-app'
            assert user_id_getter == mock_user_id_getter

            return mock_logger

        observed_logger = elastic_logger(
            'a fun URI that is really great',
            'me',
            'please',
            'my-app',
            elastic_factory=lambda c: mock_ds_class(c),
            logger_factory=__logger_factory,
            user_id_getter=mock_user_id_getter
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
        mock_do_factory_setter = Mock()
        elastic_logger(
            'a fun URI that is really great',
            'me',
            'please',
            'my-app',
            elastic_factory=lambda _: mock_ds_class,
            do_factory_setter=lambda d: mock_do_factory_setter(d)
        )
        mock_do_factory_setter.assert_called_once_with(mock_ds_class)
