# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable
from unittest.mock import MagicMock, Mock, PropertyMock, create_autospec, patch

import pytest

from tol.api_base.controller import Controller
from tol.api_base.misc import LegacyAggregationBody, LegacyAggregationParameters, ListGetParameters
from tol.api_base.misc.auth_context import AuthContext
from tol.api_client.exception import (
    ObjectNotFoundByIdException,
    RecursiveRelationNotFoundException,
    UninheritedOperationError,
    UnsupportedOperationError,
)
from tol.api_client.view import DefaultView, View
from tol.core import DataSource, DataSourceError, DataSourceFilter, ReqFieldsTree, core_data_object
from tol.core.data_object import DataObject
from tol.core.operator import DetailGetter, LegacyAggregator, PageGetter, Relational


class _TestDataSource1(DataSource, DetailGetter):

    def get_by_id(self, object_type: str, object_ids: Iterable[str], *args, **kwargs):
        return [
            self.data_object_factory(object_type, {'id': object_id}) for object_id in object_ids
        ]

    @property
    def supported_types(self):
        return ['test2', 'test1']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _TestDataSource2(DataSource, PageGetter):
    def get_list_page(self, object_type: str, *args, **kwargs):
        return [self.data_object_factory(object_type, id_=str(i)) for i in range(20)], 20

    @property
    def supported_types(self):
        return ['test_A', 'test_B']

    @property
    def attribute_types(self) -> Dict:
        return {'test_A': {}, 'test_B': {}}


class _TestDataSource3(DataSource, LegacyAggregator, PageGetter):
    """Accounts for page number and size in results"""

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        **kwargs,
    ):
        return [
            self.data_object_factory(
                object_type,
                id_=str(i + 1 + page_size * page_number),
                attributes={
                    'page': page_number,
                    'page_size': page_size,
                    'filter': object_filters.exact['column1'],
                    'sort_by': sort_by,
                },
            )
            for i in range(page_size)
        ], 560  # a very arbitrary number

    def get_aggregations_legacy(
        self, object_type: str, aggregations: Dict, object_filters: DataSourceFilter = None
    ) -> Dict:
        return {
            'completed_over_time': {
                'buckets': [
                    {
                        'key_as_string': '2015-04-01T00:00:00.000Z',
                        'key': 1427846400000,
                        'doc_count': 3,
                    },
                    {
                        'key_as_string': '2015-05-01T00:00:00.000Z',
                        'key': 1430438400000,
                        'doc_count': 0,
                    },
                ]
            }
        }

    @property
    def supported_types(self):
        return ['test_X']

    @property
    def attribute_types(self):
        return {'test_X': {}}


ds_1 = _TestDataSource1({})
ds_2 = _TestDataSource2({})
ds_3 = _TestDataSource3({})


CoreDataObject = core_data_object(ds_1, ds_2, ds_3)


class TestController:
    def test_good_object_type(self):
        expected = {
            'meta': {'total': 20, 'types': {}},
            'data': [{'type': 'test_B', 'id': str(i)} for i in range(20)],
        }
        controller = Controller(ds_2, DefaultView(ReqFieldsTree('test_B', ds_2)))
        observed = controller.get_list('test_B', ListGetParameters({}))
        rft = ReqFieldsTree('test_B', ds_2)
        controller = Controller(ds_2, DefaultView(rft), rft)
        observed = controller.get_list('test_B', ListGetParameters({}))
        assert observed == expected

    def test_not_found(self):
        """DataSource().get_by_id() returning [None] (no elements) causes 404 error"""

        class _TestDataSourceNotFound(_TestDataSource1):
            def get_by_id(self, *args, **kwargs):
                return [None]

        not_found_ds = _TestDataSourceNotFound({})
        rft = ReqFieldsTree('test2', not_found_ds)
        controller = Controller(not_found_ds, DefaultView(rft), rft)

        with pytest.raises(ObjectNotFoundByIdException):
            controller.get_detail('test2', 'anything goes too')

    def test_page_size_and_number(self):
        """Check that page_size and page_number are passed in correctly"""

        rft = ReqFieldsTree('test_X', ds_3)
        controller = Controller(ds_3, DefaultView(rft), rft)
        parsed = ListGetParameters(
            {
                'page': '90',
                'page_size': '10',
                'filter': """
                {"exact": {"column1": "value1"}}
            """,
                'sort_by': '-column1',
            }
        )
        expected = {
            'meta': {'total': 560, 'types': {}},
            'data': [
                {
                    'type': 'test_X',
                    'id': str(901 + i),
                    'attributes': {
                        'page': 90,
                        'page_size': 10,
                        'filter': 'value1',
                        'sort_by': '-column1',
                    },
                }
                for i in range(10)
            ],
        }
        observed = controller.get_list('test_X', parsed)
        assert expected == observed

    def test_aggregations(self):
        """Check that aggregations are working"""

        rft = ReqFieldsTree('test_X', ds_3)
        controller = Controller(ds_3, DefaultView(rft), rft)
        parsed = LegacyAggregationParameters(
            {
                'filter': """
                {"exact": {"column1": "value1"}}
            """
            }
        )
        body = LegacyAggregationBody(
            {
                'aggs': {
                    'completed_over_time': {
                        'date_histogram': {'field': 'complete_date', 'calendar_interval': 'month'}
                    }
                }
            }
        )
        expected = {
            'meta': {
                'aggregations': {
                    'completed_over_time': {
                        'buckets': [
                            {
                                'key_as_string': '2015-04-01T00:00:00.000Z',
                                'key': 1427846400000,
                                'doc_count': 3,
                            },
                            {
                                'key_as_string': '2015-05-01T00:00:00.000Z',
                                'key': 1430438400000,
                                'doc_count': 0,
                            },
                        ]
                    }
                },
                'types': {},
            },
            'data': [],
        }
        observed = controller.post_aggregations_legacy('test_X', parsed, body)
        assert expected == observed

    def test_unsupported_operation(self):
        """
        a DataSource that doesn't support the given operation raises
        an Exception
        """

        class _BadDataSource(DataSource):
            """Doesn't support anything"""

            def __init__(self) -> None:
                pass

            @property
            def attribute_types(self):
                raise NotImplementedError()

            @property
            def supported_types(self) -> list[str]:
                return ['no']

        bad_ds = _BadDataSource()
        rft = ReqFieldsTree('test', bad_ds)
        controller = Controller(bad_ds, DefaultView(rft), rft)
        query_args = ListGetParameters({'page': '1', 'page_size': '10'})
        with pytest.raises(UnsupportedOperationError):
            controller.get_detail('test', 'hype')
        with pytest.raises(UnsupportedOperationError):
            controller.get_list('test', query_args=query_args)
        with pytest.raises(UnsupportedOperationError):
            controller.post_aggregations_legacy('test', MagicMock(), MagicMock(), MagicMock())

    def test_operation_implemented_no_abc(self):
        """
        Operation implemented without inheriting from the correct
        ABC -> Exception
        """

        class _BadDataSource(DataSource):
            """
            Implements get_by_id without inheriting from DetailGetter
            """

            def __init__(self) -> None:
                pass

            @property
            def attribute_types(self):
                raise NotImplementedError()

            @property
            def supported_types(self) -> list[str]:
                return ['uh-oh']

            def get_by_id(self, *args, **kwargs) -> None:
                raise Exception("shouldn't have made it this far!")

        bad_ds = _BadDataSource()
        rft = ReqFieldsTree('uh-oh', bad_ds)
        controller = Controller(bad_ds, DefaultView(rft), rft)

        with pytest.raises(UninheritedOperationError) as e:
            controller.get_detail('uh-oh', 'lol')

        error_str = str(e.value)
        assert '_BadDataSource' in error_str
        assert 'get_by_id' in error_str

    def test_get_recursive_relation(self):
        """
        `Controller().get_recursive_relation()` with found object.
        """

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        expected = Mock()

        mock_view = create_autospec(View)
        mock_view.dump.return_value = expected

        mock_ds = create_autospec(Relational)
        mock_ds.get_recursive_relation.return_value = expected

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)
        observed = controller.get_recursive_relation(mock_object, ['a', 'b'])

        mock_ds.validate_to_one_recurse.assert_called_once_with('test', ['a', 'b'])
        mock_ds.get_recursive_relation.assert_called_once_with(mock_object, ['a', 'b'])
        mock_view.dump.assert_called_once_with(expected)

        assert observed == expected

    def test_get_recursive_relation_not_found(self):
        """
        `Controller().get_recursive_relation()` doesn't find object
        -> raises `RecursiveRelationNotFoundException`.
        """

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        mock_view = create_autospec(View)

        mock_ds = create_autospec(Relational)
        mock_ds.get_recursive_relation.return_value = None

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)

        with pytest.raises(RecursiveRelationNotFoundException):
            controller.get_recursive_relation(mock_object, ['a', 'b'])

        mock_ds.validate_to_one_recurse.assert_called_once_with('test', ['a', 'b'])
        mock_ds.get_recursive_relation.assert_called_once_with(mock_object, ['a', 'b'])
        mock_view.dump.assert_not_called()

    def test_get_many_relations_page(self):
        """`Controller().get_many_relations_page()`"""

        expected = [Mock() for _ in range(3)]

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        mock_view = create_autospec(View)
        mock_view.dump_bulk.side_effect = lambda i: i

        mock_params = Mock()
        type(mock_params).page = PropertyMock(return_value=3)
        type(mock_params).page_size = PropertyMock(return_value=5)

        mock_ds = create_autospec(Relational)
        mock_ds.get_to_many_relations_page.return_value = expected

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)

        controller.get_many_relations_page(mock_object, 'test_relation', mock_params)

        mock_ds.get_to_many_relations_page.assert_called_once_with(
            mock_object, 'test_relation', 3, 5
        )
        mock_view.dump_bulk.assert_called_once_with(expected)


def _make_auth_context(user_id='user1', roles=None):
    """Helper to create an AuthContext with the given user_id and roles."""
    ctx = AuthContext()
    ctx.user_id = user_id
    ctx.roles = roles or []
    return ctx


def _make_action_args(action_name='test_action', ids=None, params=None):
    """Helper to create a mock ActionParameters."""
    mock = Mock()
    type(mock).action_name = PropertyMock(return_value=action_name)
    type(mock).ids = PropertyMock(return_value=ids or ['id1', 'id2'])
    type(mock).params = PropertyMock(return_value=params or {})
    return mock


def _make_action_object(
    action_id='action1',
    flow_name=None,
    class_name=None,
    params=None,
):
    """Helper to create a mock action DataObject."""
    action = Mock()
    type(action).id = PropertyMock(return_value=action_id)
    type(action).flow_name = PropertyMock(return_value=flow_name)
    type(action).class_name = PropertyMock(return_value=class_name)
    type(action).params = PropertyMock(return_value=params)
    return action


def _make_role_action(role_id):
    """Helper to create a mock role_action with a to_one role relationship."""
    role_action = Mock()
    role_mock = Mock()
    type(role_mock).id = PropertyMock(return_value=role_id)
    role_action.to_one_relationships = {'role': role_mock}
    return role_action


def _make_role(name):
    """Helper to create a mock role DataObject."""
    role = Mock()
    type(role).name = PropertyMock(return_value=name)
    return role


def _setup_action_ds(action, role_actions=None, roles=None, user=None):
    """
    Helper to set up the action_ds mock with standard responses
    for get_list, get_one, data_object_factory, and insert.
    """
    action_ds = Mock()

    def get_list_side_effect(type_, **kwargs):
        if type_ == 'action':
            return [action]
        if type_ == 'role_action':
            return role_actions or []
        if type_ == 'role':
            return roles or []
        return []

    action_ds.get_list.side_effect = get_list_side_effect
    action_ds.get_one.return_value = user or Mock()
    action_ds.data_object_factory.return_value = Mock()
    action_ds.insert.return_value = None
    return action_ds


class TestPerformAction:
    """Tests for `Controller().perform_action()`"""

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_flow_action_success(self, mock_ctx_getter):
        """Happy path: action with flow_name inserts a flow run and user_action."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=['admin']
        )

        action = _make_action_object(flow_name='my_flow', params={'key': 'val'})
        role_action = _make_role_action('role1')
        role = _make_role('admin')
        user = Mock()

        action_ds = _setup_action_ds(
            action,
            role_actions=[role_action],
            roles=[role],
            user=user,
        )

        flow_run_result = Mock()
        type(flow_run_result).id = PropertyMock(return_value='run1')
        type(flow_run_result).name = PropertyMock(return_value='run_name_1')

        flow_ds = Mock()
        flow_ds.data_object_factory.return_value = Mock()
        flow_ds.insert.return_value = [flow_run_result]

        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        result = controller.perform_action(
            'sample_type',
            _make_action_args(action_name='test_action', ids=['id1']),
            action_ds,
            flow_ds,
        )

        assert result == ({'success': True}, 200)
        flow_ds.insert.assert_called_once()
        action_ds.insert.assert_called_once()

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_class_action_success(self, mock_ctx_getter):
        """Happy path: action with class_name instantiates and runs the class."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=['editor']
        )

        action = _make_action_object(class_name='MyAction', params={})
        role_action = _make_role_action('role1')
        role = _make_role('editor')

        action_ds = _setup_action_ds(
            action,
            role_actions=[role_action],
            roles=[role],
        )

        mock_action_class = Mock()
        mock_action_instance = Mock()
        mock_action_instance.run.return_value = 'done'
        mock_action_class.return_value = mock_action_instance

        flow_ds = Mock()
        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with patch('tol.api_base.controller.importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.MyAction = mock_action_class
            mock_import.return_value = mock_module

            result = controller.perform_action(
                'sample_type',
                _make_action_args(action_name='do_thing', ids=['id1']),
                action_ds,
                flow_ds,
            )

        assert result == ({'success': True}, 200)
        mock_action_instance.run.assert_called_once()
        action_ds.insert.assert_called_once()

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_action_not_found(self, mock_ctx_getter):
        """Action not found in action_ds raises DataSourceError 404."""

        mock_ctx_getter.return_value = _make_auth_context(user_id='user1', roles=[])

        action_ds = Mock()
        action_ds.get_list.return_value = []  # no action found

        flow_ds = Mock()
        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with pytest.raises(DataSourceError) as exc:
            controller.perform_action(
                'sample_type',
                _make_action_args(action_name='nonexistent'),
                action_ds,
                flow_ds,
            )

        assert exc.value.status_code == 404

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_unauthorized_role(self, mock_ctx_getter):
        """User missing a required role raises DataSourceError 403."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=['viewer']
        )

        action = _make_action_object(flow_name='some_flow')
        role_action = _make_role_action('role1')
        role = _make_role('admin')  # required role is 'admin'

        action_ds = _setup_action_ds(
            action,
            role_actions=[role_action],
            roles=[role],
        )

        flow_ds = Mock()
        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with pytest.raises(DataSourceError) as exc:
            controller.perform_action(
                'sample_type',
                _make_action_args(),
                action_ds,
                flow_ds,
            )

        assert exc.value.status_code == 403

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_no_flow_or_class_raises_error(self, mock_ctx_getter):
        """Action with neither flow_name nor class_name raises DataSourceError 400."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=['admin']
        )

        action = _make_action_object(flow_name=None, class_name=None)
        role_action = _make_role_action('role1')
        role = _make_role('admin')

        action_ds = _setup_action_ds(
            action,
            role_actions=[role_action],
            roles=[role],
        )

        flow_ds = Mock()
        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with pytest.raises(DataSourceError) as exc:
            controller.perform_action(
                'sample_type',
                _make_action_args(),
                action_ds,
                flow_ds,
            )

        assert exc.value.status_code == 400

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_no_roles_required_action(self, mock_ctx_getter):
        """Action with no role_actions throws error."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=[]
        )

        action = _make_action_object(flow_name='simple_flow', params={})

        action_ds = _setup_action_ds(
            action,
            role_actions=[],  # no roles required
            roles=[],
        )

        flow_run_result = Mock()
        type(flow_run_result).id = PropertyMock(return_value='run1')
        type(flow_run_result).name = PropertyMock(return_value='run_name_1')

        flow_ds = Mock()
        flow_ds.data_object_factory.return_value = Mock()
        flow_ds.insert.return_value = [flow_run_result]

        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with pytest.raises(DataSourceError) as exc:
            controller.perform_action(
                'sample_type',
                _make_action_args(),
                action_ds,
                flow_ds,
            )

        assert exc.value.status_code == 403

    @patch('tol.api_base.controller.default_ctx_getter')
    def test_class_action_import_error(self, mock_ctx_getter):
        """Class-based action with missing module raises DataSourceError 500."""

        mock_ctx_getter.return_value = _make_auth_context(
            user_id='user1', roles=['admin']
        )

        action = _make_action_object(class_name='MissingClass', params={})
        role_action = _make_role_action('role1')
        role = _make_role('admin')

        action_ds = _setup_action_ds(
            action,
            role_actions=[role_action],
            roles=[role],
        )

        flow_ds = Mock()
        mock_view = Mock()
        controller = Controller(Mock(), mock_view)

        with patch(
            'tol.api_base.controller.importlib.import_module',
            side_effect=ImportError('no module'),
        ):
            with pytest.raises(DataSourceError) as exc:
                controller.perform_action(
                    'sample_type',
                    _make_action_args(),
                    action_ds,
                    flow_ds,
                )

            assert exc.value.status_code == 500
