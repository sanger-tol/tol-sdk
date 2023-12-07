# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from string import ascii_lowercase
from unittest.mock import Mock, PropertyMock, create_autospec

import pytest

from tol.core import DataSourceError, DataSourceFilter
from tol.prefect.filter import (
    PrefectFilter,
    PrefectFilterBuilder
)


class TestPrefectFilterBuilder:
    """Functional unit tests for `PrefectFilterBuilder`"""

    def test_all_populated(self):
        """
        Test all populated:

        - fields are added as kwargs to the correct filter class
          constructor
        """

        expected = {
            'flow_filter': Mock(),
            'deployment_filter': Mock(),
            'flow_run_filter': Mock()
        }

        mock_flow_filter = Mock()
        mock_flow_filter.return_value = expected['flow_filter']

        mock_fr_filter = Mock()
        mock_fr_filter.return_value = expected['flow_run_filter']

        mock_deployment_filter = Mock()
        mock_deployment_filter.return_value = expected['deployment_filter']

        mock_map, mock_returns = self.__mock_class_map()

        builder = PrefectFilterBuilder(
            mock_fr_filter,
            mock_deployment_filter,
            mock_flow_filter,
            mock_map
        )

        builder.flow_name(['hello', 'world'])
        builder.deployment_name(['yes?', 'no!'])
        builder.id_(['test1', 'test2'])
        builder.idempotency_key(['idem1'])
        builder.name(['thing1', 'thing2'])
        builder.state(['yo'])
        builder.tags_all(list(ascii_lowercase))

        observed = builder.kwargs

        mock_map['id'].assert_called_once_with(
            any_=['test1', 'test2']
        )
        mock_map['idempotency_key'].assert_called_once_with(
            any_=['idem1']
        )
        mock_map['name'].assert_called_once_with(
            any_=['thing1', 'thing2']
        )
        mock_map['state'].assert_called_once_with(
            any_=['yo']
        )
        mock_map['tags'].assert_called_once_with(
            all_=list(ascii_lowercase)
        )
        mock_map['flow_name'].assert_called_once_with(
            any_=['hello', 'world']
        )
        mock_map['deployment_name'].assert_called_once_with(
            any_=['yes?', 'no!']
        )

        expected_fr_filters = self.__separate_flow_run_keys(
            mock_returns
        )

        mock_fr_filter.assert_called_once_with(
            **expected_fr_filters
        )
        mock_deployment_filter.assert_called_once_with(
            name=mock_returns['deployment_name']
        )
        mock_flow_filter.assert_called_once_with(
            name=mock_returns['flow_name']
        )

        assert observed == expected

    def test_mixed(self):
        """Some populated - some not"""

        expected = Mock()

        expected = {
            'flow_filter': None,
            'deployment_filter': None,
            'flow_run_filter': Mock()
        }

        mock_flow_filter = Mock()

        mock_fr_filter = Mock()
        mock_fr_filter.return_value = expected['flow_run_filter']

        mock_deployment_filter = Mock()

        mock_map, mock_returns = self.__mock_class_map()

        builder = PrefectFilterBuilder(
            mock_fr_filter,
            mock_deployment_filter,
            mock_flow_filter,
            mock_map
        )

        builder.id_(['test1', 'test2'])

        observed = builder.kwargs

        mock_map['flow_name'].assert_not_called()
        mock_map['deployment_name'].assert_not_called()
        mock_map['id'].assert_called_once_with(
            any_=['test1', 'test2']
        )
        mock_map['idempotency_key'].assert_not_called()
        mock_map['name'].assert_not_called()
        mock_map['state'].assert_not_called()
        mock_map['tags'].assert_not_called()

        mock_fr_filter.assert_called_once_with(
            id=mock_returns['id']
        )
        mock_flow_filter.assert_not_called()
        mock_deployment_filter.assert_not_called()

        assert observed == expected

    def test_none(self):
        """all `None`-d value `dict` is returned if no terms added."""

        expected = {
            'flow_run_filter': None,
            'deployment_filter': None,
            'flow_filter': None
        }

        mock_map, _ = self.__mock_class_map()

        mock_classes = [Mock() for _ in range(3)]

        builder = PrefectFilterBuilder(*mock_classes, mock_map)

        observed = builder.kwargs

        mock_map['id'].assert_not_called()
        mock_map['idempotency_key'].assert_not_called()
        mock_map['name'].assert_not_called()
        mock_map['state'].assert_not_called()
        mock_map['tags'].assert_not_called()

        for m in mock_classes:
            m.assert_not_called()

        assert observed == expected

    def __mock_class_map(
        self
    ) -> tuple[dict[str, Mock], dict[str, Mock]]:

        keys = [
            'id',
            'name',
            'idempotency_key',
            'tags',
            'state',
            'flow_name',
            'deployment_name'
        ]

        mock_map = {
            k: Mock() for k in keys
        }

        mock_returns = {
            k: Mock() for k in keys
        }
        for k, v in mock_returns.items():
            mock_map[k].return_value = v

        return mock_map, mock_returns

    def __separate_flow_run_keys(
        self,
        d: dict[str, Mock]
    ) -> dict[str, Mock]:

        return {
            k: v for k, v in d.items()
            if k not in (
                'flow_name',
                'deployment_name'
            )
        }


class TestPrefectFilter:
    """Functional unit tests for `PrefectFilter`."""

    def test_full(self):
        """Fully populated filter (every key)"""

        expected = Mock()

        ds_filter = DataSourceFilter(
            exact={
                'tags': ['a', 'b', 'c'],
                'name': 'hi'
            },
            in_list={
                'idempotency_key': ['hi', 'how'],
                'state': ['are'],
                'id': ['you?']
            }
        )

        mock_builder = create_autospec(
            PrefectFilterBuilder,
            spec_set=True
        )
        type(mock_builder).kwargs = PropertyMock(return_value=expected)

        filter_ = PrefectFilter(mock_builder)

        observed = filter_.to_kwargs(ds_filter)

        mock_builder.id_.assert_called_once_with(['you?'])
        mock_builder.idempotency_key.assert_called_once_with(
            ['hi', 'how']
        )
        mock_builder.tags_all.assert_called_once_with(
            ['a', 'b', 'c']
        )
        mock_builder.state.assert_called_once_with(['are'])
        # this should be made into a unit-length list...
        mock_builder.name.assert_called_once_with(['hi'])

        assert observed == expected

    def test_none(self):
        """
        Empty filter (no keys specified) -> no builder helpers called
        """

        expected = Mock()

        ds_filter = DataSourceFilter()

        mock_builder = create_autospec(
            PrefectFilterBuilder,
            spec_set=True
        )
        type(mock_builder).kwargs = PropertyMock(return_value=expected)

        filter_ = PrefectFilter(mock_builder)

        observed = filter_.to_kwargs(ds_filter)

        mock_builder.flow_name.assert_not_called()
        mock_builder.deployment_name.assert_not_called()
        mock_builder.id_.assert_not_called()
        mock_builder.idempotency_key.assert_not_called()
        mock_builder.tags_all.assert_not_called()
        mock_builder.state.assert_not_called()
        mock_builder.name.assert_not_called()

        assert observed == expected

    def test_single_tag(self):
        """single (non-list) tag is accepted for `exact` key"""

        ds_filter = DataSourceFilter(
            exact={
                'tags': 'single_tag'
            }
        )

        mock_builder = create_autospec(
            PrefectFilterBuilder,
            spec_set=True
        )

        filter_ = PrefectFilter(mock_builder)

        filter_.to_kwargs(ds_filter)

        mock_builder.tags_all.assert_called_once_with(
            ['single_tag']
        )

    def test_bad(self):
        """
        Raise a `DataSourceError` for:

        - any `range` or `contains`
        - `in_list` for `tags`
        - `list[str]` value in `exact` for anything but `tags`
        - non-existent attribute key
        """

        mock_builder = create_autospec(
            PrefectFilterBuilder,
            spec_set=True
        )

        filter_ = PrefectFilter(mock_builder)

        # invalid `range` and `contains filters`
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    contains={'yo': 'yes'}
                )
            )
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    range={'yo': 'yes'}
                )
            )
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    contains={'yo': 'yes'},
                    range={'yo': 'yes'}
                )
            )

        # in_list for tags
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    in_list={
                        'tags': ['matters', 'not']
                    }
                )
            )

        # `list[str]` exact value for anything but tags
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    exact={'id': ['no']}
                )
            )
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    exact={'idempotency_key': ['no']}
                )
            )
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    exact={'name': ['no']}
                )
            )
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    exact={'state': ['no']}
                )
            )

        # bad key
        with pytest.raises(DataSourceError):
            filter_.to_kwargs(
                DataSourceFilter(
                    exact={'fake': 'absolutely'}
                )
            )
