# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest

import tol.board.utils as board_utils_module
from tol.api_base.auth import ForbiddenError
from tol.api_base.misc import AuthContext
from tol.board.errors import PayloadError
from tol.board.utils import (
    check_auth_and_required_fields,
    collect_recursive,
    generate_entity_id,
    get_entity_and_child_type_from_parent_id,
    get_parent_joiner_objs,
    serialise_board_entities,
)
from tol.sql import SqlDataSource

from .utils import mock_board_get_list, mock_board_hierarchy, mock_board_obj


class TestGenerateEntityId:

    def test_known_types_use_prefix_mappings(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Each known type uses its mapped prefix."""

        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: 'xxxxxxxxxxxx')

        assert generate_entity_id('board') == 'b_xxxxxxxxxxxx'
        assert generate_entity_id('view') == 'v_xxxxxxxxxxxx'
        assert generate_entity_id('zone') == 'z_xxxxxxxxxxxx'
        assert generate_entity_id('component') == 'c_xxxxxxxxxxxx'

    def test_unknown_type_uses_fallback_prefix(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unknown type falls back to first letter of type name."""

        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: 'xxxxxxxxxxxx')

        assert generate_entity_id('widget') == 'w_xxxxxxxxxxxx'

    def test_explicit_fallback_prefix_is_used(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicit fallback_prefix is used for unknown types."""

        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: 'xxxxxxxxxxxx')

        assert generate_entity_id('widget', fallback_prefix='x') == 'x_xxxxxxxxxxxx'

    def test_id_length(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The suffix part is exactly 12 characters."""

        suffix_parts: list[str] = []
        monkeypatch.setattr(
            board_utils_module, 'generate',
            lambda alphabet, size: suffix_parts.append(str(size)) or 'x' * size
        )
        result = generate_entity_id('board')
        assert suffix_parts == ['12']
        assert result == 'b_xxxxxxxxxxxx'


class TestGetEntityAndChildTypeFromParentId:

    @pytest.mark.parametrize('parent_id,expected_parent,expected_child', [
        ('b_abc123456789', 'board', 'view'),
        ('v_abc123456789', 'view', 'zone'),
        ('z_abc123456789', 'zone', 'component'),
    ])
    def test_known_prefixes(
        self, parent_id: str, expected_parent: str, expected_child: str
    ) -> None:
        """Known prefixes return the correct parent and child types."""

        parent_type, child_type = get_entity_and_child_type_from_parent_id(parent_id)
        assert parent_type == expected_parent
        assert child_type == expected_child

    def test_leaf_type_returns_none_child(self) -> None:
        """component is the leaf; child_type is None rather than raising."""

        parent_type, child_type = get_entity_and_child_type_from_parent_id('c_abc123456789')
        assert parent_type == 'component'
        assert child_type is None

    def test_unknown_prefix_raises(self) -> None:
        """Unknown prefix raises ValueError."""
        with pytest.raises(ValueError, match='Unrecognized parent ID prefix'):
            get_entity_and_child_type_from_parent_id('x_abc123456789')


class TestCheckAuthAndRequiredFields:

    def test_unauthenticated_raises_forbidden(self) -> None:
        """Unauthenticated user raises ForbiddenError."""

        ctx = AuthContext()
        with pytest.raises(ForbiddenError):
            check_auth_and_required_fields(lambda: ctx, {})

    def test_authenticated_no_required_fields(self) -> None:
        """Authenticated user with no required fields should not raise."""

        ctx = AuthContext()
        ctx.user_id = '42'
        check_auth_and_required_fields(lambda: ctx, {})  # should not raise

    def test_missing_required_field_raises_payload_error(self) -> None:
        """Authenticated user missing required field raises PayloadError."""

        ctx = AuthContext()
        ctx.user_id = '42'
        with pytest.raises(PayloadError):
            check_auth_and_required_fields(
                lambda: ctx,
                {'other': 'value'},
                required_fields=['title'],
            )

    def test_all_required_fields_present(self) -> None:
        """Authenticated user with all required fields should not raise."""

        ctx = AuthContext()
        ctx.user_id = '42'
        check_auth_and_required_fields(
            lambda: ctx,
            {'title': 'Board', 'desc': 'x'},
            required_fields=['title', 'desc'],
        )  # should not raise


class TestGetParentJoinerObjs:

    def test_returns_filtered_joiners(self) -> None:
        """get_parent_joiner_objs returns the correct joiner objects."""

        board_ds = create_autospec(SqlDataSource, spec_set=True)

        j1 = mock_board_obj('zone_view', 'j1')
        j2 = mock_board_obj('zone_view', 'j2')
        board_ds.get_list.return_value = [j1, j2]

        result = get_parent_joiner_objs(board_ds, 'v_abc', 'zone_view')

        assert result == [j1, j2]
        cast(MagicMock, board_ds).get_list.assert_called_once()
        call_kwargs = cast(MagicMock, board_ds).get_list.call_args
        assert call_kwargs.args[0] == 'zone_view'
        assert call_kwargs.kwargs['object_filters'].and_['view.id']['eq']['value'] == 'v_abc'

    def test_empty_result(self) -> None:
        """get_parent_joiner_objs returns an empty list when no joiners are found."""

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        board_ds.get_list.return_value = []

        result = get_parent_joiner_objs(board_ds, 'v_abc', 'zone_view')
        assert result == []


class TestCollectRecursive:

    def test_leaf_type_returns_only_itself(self, type_hierarchy: list) -> None:
        """collect_recursive on the leaf type (component) returns just that type."""

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        comp = mock_board_obj('component', 'c_1')

        result = collect_recursive(board_ds, 'component', [comp])

        assert list(result.keys()) == ['component']
        assert result['component'] == [comp]
        board_ds.get_list.assert_not_called()

    def test_collects_children_recursively(self, type_hierarchy: list) -> None:
        """collect_recursive on a view with zones collects view, zone_view, and zone."""

        hierarchy = {
            'component': {},
            'zone': {
                'z_1': ('100', []),
                'z_2': ('100', []),
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_2']),
            },
            'board': {},
        }
        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)
        board_ds = create_autospec(SqlDataSource, spec_set=True)
        board_ds.get_list.side_effect = mock_board_get_list(objs)

        result = collect_recursive(board_ds, 'view', [objs['view']['v_a']])

        assert len(result['view']) == 1
        assert len(result['zone']) == 2
        assert len(result['zone_view']) == 2

        component_calls = [
            c for c in cast(MagicMock, board_ds).get_list.call_args_list
            if c.args[0] == 'component_zone'
        ]
        assert len(component_calls) == 2  # one per zone


class TestSerialiseBoardEntities:

    def test_unknown_parent_id_returns_empty(self) -> None:
        """
        serialise board entities with a parent id that doesn't match any entity returns empty dict.
        """

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        result = serialise_board_entities({'view': [], 'zone_view': []}, 'v_missing', board_ds)
        assert result == {}

    def test_zone_includes_data_source_fields(self, type_hierarchy: list) -> None:
        """serialise board entities includes data source fields for a zone."""

        zone = mock_board_obj('zone', 'z_1', attributes={'title': 'My Zone'})
        zone.data_source_instance.id = 'dsi_42'
        zone.data_source_instance.ui_api_details = {'url': 'http://example.com'}

        board_ds = create_autospec(SqlDataSource, spec_set=True)

        result = serialise_board_entities({'zone': [zone]}, 'z_1', board_ds)

        assert result['id'] == 'z_1'
        assert result['type'] == 'zone'
        assert result['data_source_instance_id'] == 'dsi_42'
        assert result['ui_api_details'] == {'url': 'http://example.com'}

    def test_board_includes_owner_and_write_privilege(self, type_hierarchy: list) -> None:
        """serialise board entities for a board includes owner email and write_privilege."""

        board = mock_board_obj('board', 'b_1', attributes={'title': 'My Board'}, user_id='42')
        board.user.oidc_id = 'user@example.com'
        board.user.id = '42'

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        ctx = AuthContext()
        ctx.user_id = '42'

        result = serialise_board_entities(
            {'board': [board]}, 'b_1', board_ds, ctx_getter=lambda: ctx
        )

        assert result['owner_email'] == 'user@example.com'
        assert result['write_privilege'] is True

    def test_board_write_privilege_false_when_different_user(self) -> None:
        """
        Serialise board entities for a board returns
        write_privilege False when current user is not the owner.
        """

        board = mock_board_obj('board', 'b_1', attributes={'title': 'My Board'}, user_id='99')
        board.user.oidc_id = 'other@example.com'
        board.user.id = '99'

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        ctx = AuthContext()
        ctx.user_id = '42'

        result = serialise_board_entities(
            {'board': [board]}, 'b_1', board_ds, ctx_getter=lambda: ctx
        )

        assert result['write_privilege'] is False

    def test_board_write_privilege_true_for_warden(self) -> None:
        """
        A warden user gets write_privilege=True even if they don't own the board.
        """

        board = mock_board_obj('board', 'b_1', attributes={'title': 'My Board'}, user_id='99')
        board.user.oidc_id = 'owner@example.com'
        board.user.id = '99'

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        ctx = AuthContext()
        ctx.user_id = '42'
        ctx.roles = ['warden']

        result = serialise_board_entities(
            {'board': [board]}, 'b_1', board_ds, ctx_getter=lambda: ctx
        )

        assert result['write_privilege'] is True

    def test_view_children_ordered_by_joiner_order(self, type_hierarchy: list) -> None:
        """
        Serialise board entities orders view children
        according to the order field on the joiner objects.
        """

        hierarchy = {
            'component': {},
            'zone': {
                'z_1': ('100', []),
                'z_2': ('100', []),
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_2']),
            },
            'board': {},
        }
        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        # set explicit order on joiners so z_2 comes first
        joiner_objs = list(objs['zone_view'].values())
        joiner_objs[0].order = 1  # z_1 joiner
        joiner_objs[1].order = 0  # z_2 joiner

        all_entities = {
            'view': list(objs['view'].values()),
            'zone': list(objs['zone'].values()),
            'zone_view': joiner_objs,
        }
        board_ds = create_autospec(SqlDataSource, spec_set=True)

        result = serialise_board_entities(all_entities, 'v_a', board_ds)

        assert result['type'] == 'view'
        # z_2 should appear first because its joiner order is 0
        assert result['order'][0] == 'z_2'
        assert result['order'][1] == 'z_1'

    def test_id_mapping_remaps_ids_in_output(self) -> None:
        """
        Serialise board entities remaps entity IDs in
        the output according to the provided id_mapping.
        """

        zone = mock_board_obj('zone', 'z_old', attributes={'title': 'Z'})

        board_ds = create_autospec(SqlDataSource, spec_set=True)
        id_mapping = {'z_old': 'z_new'}

        result = serialise_board_entities({'zone': [zone]}, 'z_old', board_ds, id_mapping)

        assert result['id'] == 'z_new'
