# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, PropertyMock, call, create_autospec

from prefect.client.orchestration import PrefectClient
from prefect.client.schemas.objects import Flow
from prefect.client.schemas.responses import DeploymentResponse
from prefect.client.schemas.sorting import FlowRunSort
from prefect.exceptions import ObjectNotFound

import pytest

from tol.core import DataSourceError, DataSourceFilter
from tol.prefect import PrefectDataSource
from tol.prefect.converter import (
    DefaultObjectConverter,
    DefaultPrefectConverter
)
from tol.prefect.filter import PrefectFilter
from tol.prefect.prefect_object import FlowRunObject


class TestPrefectDataSource(IsolatedAsyncioTestCase):

    def test_get_by_id_bad_type(self):
        """
        calling `PrefectDataSource().get_by_id()` with anything
        but "flow_run" -> raise `DataSourceError`
        """

        prefect_ds = PrefectDataSource(None, None, None, None)

        with pytest.raises(DataSourceError):
            prefect_ds.get_by_id('bad_luck', ['hype', 'train'])

    def test_get_by_id_mixed(self):
        """
        `PrefectDataSource().get_by_id()` calls the correct methods
        on its `PrefectClient` instance, and tolerates it returning
        `None` instances.
        """

        expected = [
            Mock() if i % 3 != 0 else None
            for i in range(5)
        ]

        ids = [str(i) for i in range(111, 600, 111)]

        expected_calls = [call(id_) for id_ in ids]

        return_iter = iter(expected)

        def __side_effect(__id: str) -> Optional[Mock]:
            __v = next(return_iter)
            if __v is None:
                raise ObjectNotFound(Mock())
            return __v

        mock_client = self.__mock_client()
        mock_client.read_flow_run.side_effect = __side_effect

        mock_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )
        mock_converter.async_convert_iterable.return_value = expected

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            None,
            None,
            lambda: mock_converter
        )

        observed = prefect_ds.get_by_id('flow_run', (i for i in ids))

        assert mock_client.read_flow_run.call_args_list == expected_calls
        mock_converter.async_convert_iterable.assert_called_once_with(expected)

        assert observed == expected

    def test_get_flow_run(self):
        """
        `PrefectDataSource().get_flow_run()` uses the `DetailGetter` operation
        internally.
        """

        expected = Mock()

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.get_by_id.return_value = [expected]

        observed = PrefectDataSource.get_flow_run(mock_ds, 'test_id')

        mock_ds.get_by_id.assert_called_once_with('flow_run', ['test_id'])
        assert observed == expected

    def test_get_list_page_paging(self):
        """
        Test it pages and filters correctly, and always sorts
        by ID descending
        """

        expected = [Mock() for _ in range(3)]

        mock_client = self.__mock_client()
        mock_client.read_flow_runs.return_value = expected

        mock_ds_filter = create_autospec(DataSourceFilter, spec_set=True)

        mock_filter_result = {
            k: Mock()
            for k in ('flow_run_filter', 'deployment_filter', 'flow_filter')
        }

        mock_filter = create_autospec(PrefectFilter, spec_set=True)
        mock_filter.to_kwargs.return_value = mock_filter_result

        mock_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )
        mock_converter.async_convert_iterable.return_value = expected

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            lambda: mock_filter,
            None,
            lambda: mock_converter
        )

        (observed, _) = prefect_ds.get_list_page(
            'flow_run',
            11,
            3,
            mock_ds_filter
        )

        mock_filter.to_kwargs.assert_called_once_with(
            mock_ds_filter
        )
        mock_client.read_flow_runs.assert_called_once_with(
            **mock_filter_result,
            sort=FlowRunSort.ID_DESC,
            limit=3,
            offset=30
        )
        mock_converter.async_convert_iterable.assert_called_once_with(
            expected
        )

        assert observed == expected

    def test_get_list_page_paging_filter_none(self):
        """
        Test it pages correctly when given no filters
        """

        expected = [Mock() for _ in range(3)]

        mock_client = self.__mock_client()
        mock_client.read_flow_runs.return_value = expected

        mock_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )
        mock_converter.async_convert_iterable.return_value = expected

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            None,
            None,
            lambda: mock_converter
        )

        (observed, _) = prefect_ds.get_list_page('flow_run', 11, 3)

        mock_client.read_flow_runs.assert_called_once_with(
            sort=FlowRunSort.ID_DESC,
            limit=3,
            offset=30
        )
        mock_converter.async_convert_iterable.assert_called_once_with(
            expected
        )

        assert observed == expected

    def test_get_list_page_sort(self):
        """raise `DataSourceError` if trying to sort"""

        mock_client = self.__mock_client()

        mock_ds_filter = create_autospec(DataSourceFilter, spec_set=True)

        mock_filter = create_autospec(PrefectFilter, spec_set=True)

        mock_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            lambda: mock_filter,
            None,
            lambda: mock_converter
        )

        with pytest.raises(DataSourceError):
            prefect_ds.get_list_page(
                'flow_run',
                2309,
                23,
                object_filters=mock_ds_filter,
                sort_by='down - bad!'
            )

    def test_get_list_page_bad_type(self):
        """
        `PrefectDataSource().get_list_page()`
        with `object_typetype != 'flow_run'` ->
        raises `DataSourceError`.
        """

        mock_client = self.__mock_client()
        mock_filter = create_autospec(PrefectFilter, spec_set=True)
        mock_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            lambda: mock_filter,
            None,
            lambda: mock_converter
        )

        with pytest.raises(DataSourceError):
            prefect_ds.get_list_page(
                'bad_type',
                2309,
                23
            )

    def test_get_list(self):
        """Calls `.get_list_page()` internally"""

        mock_prefect_ds = create_autospec(
            PrefectDataSource,
            spec_set=True
        )
        mock_prefect_ds.get_page_size.return_value = 3

        mock_ds_filter = create_autospec(DataSourceFilter, spec_set=True)

        expected = [Mock() for _ in range(7)]

        starts = list(range(0, 7, 3))

        expected_calls = [
            call(
                'flow_run',
                i + 1,
                page_size=3,
                object_filters=mock_ds_filter
            )
            for i in range(4)
        ]

        iter_steps = enumerate(starts, start=1)

        def __get_list_page(
            type_: str,
            n: int,
            page_size: int = None,
            object_filters=None,
            sort_by=None
        ) -> list[Mock]:

            assert type_ == 'flow_run'
            assert page_size == 3
            assert object_filters == mock_ds_filter
            assert sort_by is None

            try:
                i, stop = next(iter_steps)
                assert i == n

                return expected[stop:stop + 3], None
            except StopIteration:
                return [], None

        mock_prefect_ds.get_list_page.side_effect = __get_list_page

        observed = list(
            PrefectDataSource.get_list(
                mock_prefect_ds,
                'flow_run',
                object_filters=mock_ds_filter
            )
        )

        assert mock_prefect_ds.get_list_page.call_args_list == (
            expected_calls
        )
        assert observed == expected

    async def test_get_names(self):
        """
        `PrefectDataSource().get_names()` uses
        the given `PrefectClient` instance's
        read by ID methods.
        """

        expected = ('test flow', 'test deployment')

        mock_deployment = create_autospec(
            DeploymentResponse,
            spec_set=True
        )
        type(mock_deployment).name = PropertyMock(
            return_value='test deployment'
        )
        type(mock_deployment).flow_id = PropertyMock(
            return_value='a fun flow ID'
        )

        mock_flow = create_autospec(Flow, spec_set=True)
        type(mock_flow).name = PropertyMock(
            return_value='test flow'
        )

        mock_client = self.__mock_client()
        mock_client.read_deployment.return_value = mock_deployment
        mock_client.read_flow.return_value = mock_flow

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = await prefect_ds.get_names('a fun deployment ID')

        mock_client.read_deployment.assert_called_once_with(
            'a fun deployment ID'
        )
        mock_client.read_flow.assert_called_once_with(
            'a fun flow ID'
        )
        assert observed == expected

    async def test_get_deployment_id(self):
        """`PrefectDataSource().get_deployment_id()`"""

        expected = 'excellent IDEA'

        mock_dep = create_autospec(DeploymentResponse, spec_set=True)
        type(mock_dep).id = PropertyMock(return_value=expected)

        mock_client = self.__mock_client()
        mock_client.read_deployment_by_name.return_value = mock_dep

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = await prefect_ds.get_deployment_id('hype', 'train')

        mock_client.read_deployment_by_name.assert_called_once_with(
            'hype/train'
        )
        assert observed == expected

    def test_insert_flow_run_iterable(self):
        """
        `PrefectDataSource().insert_flow_run_iterable()` internally calls
        `PrefectDataSource().insert()` with `object_type="flow_run"`
        """

        expected = (Mock() for _ in range(3))

        mock_objs = (Mock() for _ in range(3))

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.insert.return_value = expected

        observed = PrefectDataSource.insert_flow_run_iterable(mock_ds, mock_objs)

        mock_ds.insert.assert_called_once_with('flow_run', mock_objs)
        assert observed == expected

    def test_insert_flow_run(self):
        """
        `PrefectDataSource().insert_flow_run()` internally calls
        `PrefectDataSource().insert_flow_run_iterable()` with a singleton `list`
        """

        expected = Mock()

        mock_obj = Mock()

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.insert_flow_run_iterable.return_value = (c for c in [expected])

        observed = PrefectDataSource.insert_flow_run(mock_ds, mock_obj)

        mock_ds.insert_flow_run_iterable.assert_called_once_with([mock_obj])
        assert observed == expected

    def test_insert(self):
        """
        `PrefectDataSource().insert()` calls the correct methods on its
        injected dependencies.
        """

        expected = [Mock() for _ in range(3)]

        mock_objs = [
            self.__mock_flow_run_object(
                attributes={str(i): i}
            )
            for i in range(3)
        ]

        mock_flow_runs = [Mock() for _ in range(3)]

        mock_kwargs = [
            {
                'name': str(i),
                'deployment_id': 'lol'
            }
            for i in range(3)
        ]

        expected_client_calls = [
            call(**k) for k in mock_kwargs
        ]

        mock_object_converter = create_autospec(
            DefaultObjectConverter,
            spec_set=True
        )
        mock_object_converter.async_convert_iterable.return_value = (
            mock_kwargs
        )

        mock_prefect_converter = create_autospec(
            DefaultPrefectConverter,
            spec_set=True
        )
        mock_prefect_converter.async_convert_iterable.return_value = (
            expected
        )

        mock_fr_iter = iter(mock_flow_runs)

        def __side_effect(*__args, **__kwargs):
            return next(mock_fr_iter)

        mock_client = self.__mock_client()
        mock_client.create_flow_run_from_deployment.side_effect = (
            __side_effect
        )

        prefect_ds = PrefectDataSource(
            lambda: mock_client,
            None,
            lambda: mock_object_converter,
            lambda: mock_prefect_converter
        )

        observed = list(
            prefect_ds.insert('flow_run', mock_objs)
        )

        mock_object_converter.async_convert_iterable.assert_called_once_with(
            mock_objs
        )
        assert mock_client.create_flow_run_from_deployment.call_args_list == (
            expected_client_calls
        )
        mock_prefect_converter.async_convert_iterable.assert_called_once_with(
            mock_flow_runs
        )

        assert observed == expected

    def __mock_flow_run_object(
        self,
        id_: Optional[str] = None,
        attributes: dict[str, Any] = {}
    ) -> Mock:

        mock_obj = create_autospec(FlowRunObject, spec_set=True)

        type(mock_obj).id = PropertyMock(return_value=id_)
        type(mock_obj).attributes = PropertyMock(return_value=attributes)

        return mock_obj

    def __mock_client(self) -> Mock:
        """Creates an async ContextManger mock for PrefectClient"""

        mock_client = create_autospec(PrefectClient, spec_set=True)
        mock_client.__aenter__.return_value = mock_client

        return mock_client
