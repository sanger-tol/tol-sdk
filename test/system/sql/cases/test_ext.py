# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.database import DefaultDatabase

from .. import models
from ..base_case import DatabaseTestCase, models_list, session_factory


class TestDatabaseExt(DatabaseTestCase):
    """
    Tests a real database with ext column.
    """

    def test_json_default_name(self):
        """JSON-type, default (`ext`) name"""
        with session_factory() as sess:
            sess.add(
                models.ExtDefault(
                    id='yes'  # noqa
                )
            )
            sess.add(
                models.ExtDefault(
                    id='fun',
                    string_column='neverending',
                    ext={
                        'hype': 'train'
                    }
                )
            )
            sess.commit()

        db = DefaultDatabase(session_factory, models_list)

        # no ext
        attrs = db.get_by_id('ext_default', 'yes').instance_attributes
        assert attrs == {
            'string_column': None
        }

        # includes ext
        attrs = db.get_by_id('ext_default', 'fun').instance_attributes
        assert attrs == {
            'hype': 'train',
            'string_column': 'neverending'
        }

    def test_jsonb_override_name_nullable(self):
        """JSONB-type, override name, nullable"""

        with session_factory() as sess:
            sess.add(
                models.ExtOverride(
                    id='1'  # noqa
                )
            )
            sess.add(
                models.ExtOverride(
                    id='2',  # noqa
                    string_column='neverending',
                    ext_lol={
                        'hype': 'train'
                    }
                )
            )
            sess.commit()

        db = DefaultDatabase(session_factory, models_list)

        results = [
            m.instance_attributes
            for m in db.get_page('ext_override')
        ]

        assert results == [
            {
                'string_column': None
            },
            {
                'string_column': 'neverending',
                'hype': 'train'
            }
        ]
