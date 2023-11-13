# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

from tol.log import elastic_logger


class TestElasticLogger:
    """Tests the `elastic_logger` factory function"""

    def test_arguments(self):
        """Tests arguments are passed in correctly"""

        mock_ds_class = Mock()
        expected = Mock()
        mock_ds_class.return_value = expected

        observed = elastic_logger(
            'a fun URI that is really great',
            'me',
            'please',
            factory=lambda c: mock_ds_class(c)
        )
        assert expected == observed

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
