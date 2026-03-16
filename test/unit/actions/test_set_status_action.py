# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase
from unittest.mock import MagicMock

from tol.actions import SetStatusAction


def _make_datasource(ids, object_type, status_type_id):
    """
    Build a MagicMock datasource wired up for a successful run.

    Returns (datasource, status_type, status_objects, parents).
    """
    datasource = MagicMock()

    # Use a plain string so setattr(parent, status_type, obj) in the action works.
    status_type = status_type_id
    parents = {id_: MagicMock(name=f'parent_{id_}') for id_ in ids}

    def get_one(table, id_):
        if table == f'{object_type}_status_type':
            return status_type
        return parents.get(id_, MagicMock())

    datasource.get_one.side_effect = get_one

    status_objects = [MagicMock(name=f'status_{id_}') for id_ in ids]
    for obj, id_ in zip(status_objects, ids):
        obj.to_one_relationships.get.return_value = parents[id_]

    datasource.data_object_factory.side_effect = list(status_objects)

    session = datasource.get_session.return_value.__enter__.return_value

    # Consume the generator argument so that get_one and data_object_factory
    # are actually called, then return the same objects for the for-loop in run().
    def insert_side_effect(table, objects):
        consumed = list(objects)
        return iter(consumed)

    session.insert.side_effect = insert_side_effect

    return datasource, status_type, status_objects, parents


class TestSetStatusAction(TestCase):

    def setUp(self):
        self.action = SetStatusAction()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_missing_params_returns_400(self):
        datasource = MagicMock()
        result, code = self.action.run(
            datasource=datasource,
            ids=['id1'],
            object_type='specimen',
            params=None,
        )
        self.assertEqual(code, 400)
        self.assertEqual(result, {'error': 'Missing required param: "status"'})
        datasource.get_one.assert_not_called()

    def test_missing_status_key_returns_400(self):
        datasource = MagicMock()
        result, code = self.action.run(
            datasource=datasource,
            ids=['id1'],
            object_type='specimen',
            params={},
        )
        self.assertEqual(code, 400)
        self.assertEqual(result, {'error': 'Missing required param: "status"'})
        datasource.get_one.assert_not_called()

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_success_returns_200(self):
        ids = ['id1', 'id2']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')

        result, code = self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        self.assertEqual(code, 200)
        self.assertEqual(result, {'success': True})

    def test_status_type_fetched_from_correct_table(self):
        ids = ['id1']
        object_type = 'sample'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'pending')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'pending'},
        )

        datasource.get_one.assert_any_call('sample_status_type', 'pending')

    def test_parent_fetched_for_each_id(self):
        ids = ['id1', 'id2', 'id3']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        for id_ in ids:
            datasource.get_one.assert_any_call(object_type, id_)

    def test_data_object_factory_called_once_per_id(self):
        ids = ['id1', 'id2']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        self.assertEqual(datasource.data_object_factory.call_count, len(ids))

    def test_session_insert_called_with_correct_status_table(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')
        session = datasource.get_session.return_value.__enter__.return_value

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        insert_call_args = session.insert.call_args
        self.assertEqual(insert_call_args[0][0], 'specimen_status')

    def test_session_upsert_called_for_each_inserted_object(self):
        ids = ['id1', 'id2']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')
        session = datasource.get_session.return_value.__enter__.return_value

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        self.assertEqual(session.upsert.call_count, len(ids))

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_get_one_exception_returns_500(self):
        datasource = MagicMock()
        datasource.get_one.side_effect = Exception('DB connection failed')

        result, code = self.action.run(
            datasource=datasource,
            ids=['id1'],
            object_type='specimen',
            params={'status': 'active'},
        )

        self.assertEqual(code, 500)
        self.assertEqual(result, {'error': 'DB connection failed'})

    def test_session_insert_exception_returns_500(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _, _ = _make_datasource(ids, object_type, 'active')
        session = datasource.get_session.return_value.__enter__.return_value
        session.insert.side_effect = Exception('Insert failed')

        result, code = self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'status': 'active'},
        )

        self.assertEqual(code, 500)
        self.assertEqual(result, {'error': 'Insert failed'})
