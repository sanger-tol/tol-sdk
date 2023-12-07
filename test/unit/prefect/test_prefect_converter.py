# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from string import ascii_lowercase
from typing import Any, Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, PropertyMock, call, create_autospec
from uuid import uuid4

from prefect.client.schemas.objects import FlowRun

import pytest

from tol.core import DataObject, DataSourceError
from tol.prefect import PrefectDataSource
from tol.prefect.converter import (
    DefaultObjectConverter,
    DefaultPrefectConverter
)


class TestDefaultPrefectConverter(IsolatedAsyncioTestCase):

    async def test_convert(self):
        """
        `DefaultPrefectConverter().convert` with good data
        """

        expected = create_autospec(DataObject, spec_set=True)

        dep_id = uuid4()

        mock_fr = self.__mock_flow_run(
            'AAAAAA',
            'hello',
            dep_id,
            'star',
            list(ascii_lowercase),
            'hahahaha',
            {c: f'test_{c}' for c in 'abc'}
        )

        mock_do_factory = Mock()
        mock_do_factory.return_value = expected

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        type(mock_ds).data_object_factory = mock_do_factory
        mock_ds.get_names.return_value = ('tom', 'jerry')

        converter = DefaultPrefectConverter(mock_ds)
        observed = await converter.async_convert(mock_fr)

        mock_ds.get_names.assert_called_once_with(dep_id)
        mock_do_factory.assert_called_once_with(
            'flow_run',
            'AAAAAA',
            attributes={
                'name': 'hello',
                'deployment_name': 'jerry',
                'flow_name': 'tom',
                'state': 'star',
                'tags': list(ascii_lowercase),
                'idempotency_key': 'hahahaha',
                'parameters': {
                    'a': 'test_a',
                    'b': 'test_b',
                    'c': 'test_c'
                }
            }
        )
        assert observed == expected

    async def test_names_cache(self):
        """
        The fetching of flow and deployment names is memoised,
        and only occurs once for a given `deployment_id`. With
        3 unique deployment ID's, there should only be 3 calls
        to `PrefectDataSource().get_names()`.
        """

        expected_calls = [
            call(f'ID_{i}') for i in range(3)
        ]

        in_ = [
            self.__mock_flow_run(
                'liek an ID',
                '__name__',
                f'ID_{i % 3}',
                'yooooooo',
                [],
                'sdksdj',
                {}
            )
            if i % 5 != 3 else None
            for i in range(7)
        ]

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.get_names.return_value = (Mock(), Mock())

        converter = DefaultPrefectConverter(mock_ds)

        list(await converter.async_convert_iterable(in_))

        assert mock_ds.get_names.call_args_list == expected_calls

    def __mock_flow_run(
        self,
        id_: str,
        name: str,
        dep_id: str,
        state_name: str,
        tags: list[str],
        idempotency_key: str,
        parameters: dict[str, Any]
    ) -> Mock:

        mock_fr = create_autospec(FlowRun, spec_set=True)

        type(mock_fr).id = PropertyMock(return_value=id_)
        type(mock_fr).name = PropertyMock(return_value=name)
        type(mock_fr).deployment_id = PropertyMock(return_value=dep_id)
        type(mock_fr).state_name = PropertyMock(return_value=state_name)
        type(mock_fr).tags = PropertyMock(return_value=tags)
        type(mock_fr).idempotency_key = PropertyMock(
            return_value=idempotency_key
        )
        type(mock_fr).parameters = PropertyMock(
            return_value=parameters
        )

        return mock_fr


class TestDefaultObjectConverter(IsolatedAsyncioTestCase):

    async def test_convert_good(self):
        """`DefaultObjectConverter().async_convert()` with good data"""

        expected = {
            'deployment_id': 'sdlkjskldo8',
            'name': 'gander drake',
            'parameters': {'a': 'A', 'b': 'B', 'c': 'C'},
            'tags': list(ascii_lowercase),
            'idempotency_key': 'yes'
        }

        mock_obj = self.__mock_object(
            attributes={
                'flow_name': 'hype',
                'deployment_name': 'train',
                'name': 'gander drake',
                'tags': list(ascii_lowercase),
                'idempotency_key': 'yes',
                'parameters': {
                    c: c.upper() for c in 'abc'
                }
            }
        )

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.get_deployment_id.return_value = 'sdlkjskldo8'

        converter = DefaultObjectConverter(mock_ds)

        observed = await converter.async_convert(mock_obj)

        mock_ds.get_deployment_id.assert_called_once_with('hype', 'train')
        assert observed == expected

    async def test_convert_bad(self):
        """
        `DefaultObjectConverter().async_convert()` with bad data:

        - missing `flow_name`
        - missing `deployment_name`
        """

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.get_deployment_id.return_value = 'sdlkjskldo8'

        converter = DefaultObjectConverter(mock_ds)

        # missing `flow_name` and `deployment_name`
        mock_obj = self.__mock_object()
        with pytest.raises(DataSourceError):
            await converter.async_convert(mock_obj)

        # missing `flow_name`
        mock_obj = self.__mock_object(
            attributes={'deployment_name': 'skdlsjd'}
        )
        with pytest.raises(DataSourceError):
            await converter.async_convert(mock_obj)

        # missing `deployment_name`
        mock_obj = self.__mock_object(
            attributes={'flow_name': ':('}
        )
        with pytest.raises(DataSourceError):
            await converter.async_convert(mock_obj)

    async def test_cache(self):
        """
        Caching on `DefaultObjectConverter().async_convert()` means
        `PrefectDataSource().get_deployment_id()` only called
        once for each `flow_name`, `deployment_name` pair
        """

        expected = [
            {
                'deployment_id': 'Nick Cage',
                'parameters': None,
                'name': None,
                'tags': None,
                'idempotency_key': str(i)
            }
            for i in range(3)
        ]

        mock_objs = (
            self.__mock_object(
                attributes={
                    'flow_name': 'face',
                    'deployment_name': 'off',
                    'idempotency_key': str(i)
                }
            )
            for i in range(3)
        )

        mock_ds = create_autospec(PrefectDataSource, spec_set=True)
        mock_ds.get_deployment_id.return_value = 'Nick Cage'

        converter = DefaultObjectConverter(mock_ds)

        observed = list(
            await converter.async_convert_iterable(mock_objs)
        )

        mock_ds.get_deployment_id.assert_called_once_with('face', 'off')
        assert observed == expected

    def __mock_object(
        self,
        type_: str = 'flow_run',
        id_: Optional[str] = None,
        attributes: dict[str, Any] = {}
    ) -> Mock:

        mock_obj = Mock()

        type(mock_obj).type = PropertyMock(return_value=type_)
        type(mock_obj).id = PropertyMock(return_value=id_)
        type(mock_obj).attributes = PropertyMock(return_value=attributes)

        return mock_obj
