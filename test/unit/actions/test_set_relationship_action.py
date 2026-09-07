# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase
from unittest.mock import MagicMock

from tol.action.actions import SetRelationshipAction
from tol.core import DataSourceError


def _make_datasource(ids, object_type, related_id, relationship='species', related_type=None):
    """
    Build a MagicMock datasource wired up for a successful run.

    Returns (datasource, related_object, parents).
    """
    related_type = related_type or relationship
    datasource = MagicMock()
    to_one = {relationship: related_type}
    datasource.relationship_config = {
        object_type: MagicMock(to_one=to_one),
    }

    def validate_to_one_relationship(obj_type, rel_name):
        if obj_type != object_type or rel_name not in to_one:
            raise DataSourceError(
                'Bad Relationship Name',
                f'No to-one relationship "{rel_name}" exists on type {obj_type}.',
                400
            )

    datasource.validate_to_one_relationship.side_effect = validate_to_one_relationship

    related_object = MagicMock(name=f'related_{related_id}')
    parents = {id_: MagicMock(name=f'parent_{id_}') for id_ in ids}

    def get_one(table, id_):
        if table == related_type:
            return related_object
        return parents.get(id_, MagicMock())

    datasource.get_one.side_effect = get_one

    session = datasource.get_session.return_value.__enter__.return_value

    def upsert_side_effect(table, objects):
        return list(objects)

    session.upsert.side_effect = upsert_side_effect

    return datasource, related_object, parents


class TestSetRelationshipAction(TestCase):

    def setUp(self):
        self.action = SetRelationshipAction()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_missing_params_returns_400(self):
        datasource = MagicMock()
        with self.assertRaises(DataSourceError) as ctx:
            self.action.run(
                datasource=datasource,
                ids=['id1'],
                object_type='specimen',
                params=None,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        datasource.get_one.assert_not_called()

    def test_missing_relationship_key_returns_400(self):
        datasource = MagicMock()
        with self.assertRaises(DataSourceError) as ctx:
            self.action.run(
                datasource=datasource,
                ids=['id1'],
                object_type='specimen',
                params={'related_id': 'species1'},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        datasource.get_one.assert_not_called()

    def test_missing_related_id_returns_400(self):
        datasource = MagicMock()
        with self.assertRaises(DataSourceError) as ctx:
            self.action.run(
                datasource=datasource,
                ids=['id1'],
                object_type='specimen',
                params={'relationship': 'species'},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        datasource.get_one.assert_not_called()

    def test_missing_ids_returns_400(self):
        datasource = MagicMock()
        with self.assertRaises(DataSourceError) as ctx:
            self.action.run(
                datasource=datasource,
                ids=[],
                object_type='specimen',
                params={'relationship': 'species', 'related_id': 'species1'},
            )
        self.assertEqual(ctx.exception.status_code, 400)
        datasource.get_one.assert_not_called()

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_success_returns_200(self):
        ids = ['id1', 'id2']
        object_type = 'specimen'
        datasource, related_object, parents = _make_datasource(ids, object_type, 'species1')

        result, code = self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        self.assertEqual(code, 200)
        self.assertEqual(result, {'success': True})

    def test_related_object_fetched_from_related_type_table(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _ = _make_datasource(ids, object_type, 'species1')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        datasource.get_one.assert_any_call('species', 'species1')

    def test_related_object_fetched_using_relationship_config_target_type(self):
        # e.g. a "co_author" relationship on a document points to an "author" type
        ids = ['id1']
        object_type = 'document'
        datasource, _, _ = _make_datasource(
            ids, object_type, 'author1', 'co_author', 'author'
        )

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'co_author', 'related_id': 'author1'},
        )

        datasource.get_one.assert_any_call('author', 'author1')

    def test_parent_fetched_for_each_id(self):
        ids = ['id1', 'id2', 'id3']
        object_type = 'specimen'
        datasource, _, _ = _make_datasource(ids, object_type, 'species1')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        for id_ in ids:
            datasource.get_one.assert_any_call(object_type, id_)

    def test_relationship_set_on_each_parent(self):
        ids = ['id1', 'id2']
        object_type = 'specimen'
        datasource, related_object, parents = _make_datasource(ids, object_type, 'species1')

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        for parent in parents.values():
            self.assertEqual(parent.species, related_object)

    def test_session_upsert_called_with_correct_object_type(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _ = _make_datasource(ids, object_type, 'species1')
        session = datasource.get_session.return_value.__enter__.return_value

        self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        upsert_call_args = session.upsert.call_args
        self.assertEqual(upsert_call_args[0][0], 'specimen')

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_unknown_relationship_returns_400(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _ = _make_datasource(ids, object_type, 'species1')

        with self.assertRaises(DataSourceError) as ctx:
            self.action.run(
                datasource=datasource,
                ids=ids,
                object_type=object_type,
                params={'relationship': 'not_a_relationship', 'related_id': 'species1'},
            )

        self.assertEqual(ctx.exception.status_code, 400)
        datasource.get_one.assert_not_called()

    def test_get_one_exception_returns_500(self):
        ids = ['id1']
        object_type = 'specimen'
        datasource, _, _ = _make_datasource(ids, object_type, 'species1')
        datasource.get_one.side_effect = Exception('DB connection failed')

        result, code = self.action.run(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params={'relationship': 'species', 'related_id': 'species1'},
        )

        self.assertEqual(code, 500)
        self.assertIn('error', result)
