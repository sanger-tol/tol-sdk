# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.automap import automap_base

from .. import models
from ..base_case import session_factory, DatabaseTestCase


ONLY = [
    'a',
    'b',
    'r1',
    'r2',
    'r3'
]


class TestReflect(DatabaseTestCase):
    def test_reflect(self):
        # engine, suppose it has two tables 'user' and 'address' set up
        engine = create_engine(os.environ['DB_URI'])

        metadata = MetaData()

        # we can reflect it ourselves from a database, using options
        # such as 'only' to limit what tables we look at...
        metadata.reflect(engine, only=ONLY)
        # we can then produce a set of mappings from this MetaData.
        Base = automap_base(metadata=metadata)

        # calling prepare() just sets up mapped classes and relationships.
        Base.prepare()

        with session_factory() as sess:
            sess.add(
                models.R1(id_override='21')
            )
            sess.add(
                models.R3(id='thing_1', ur_r1_id='21')
            )
            sess.add(
                models.R3(id='thing_too', ur_r1_id='21')
            )
            sess.commit()

        with session_factory() as sess2:
            r1_class = Base.classes.r1
            instance_r1 = sess2.query(r1_class).filter(r1_class.id_override=='21').one_or_none()
            assert instance_r1 is not None

            r3_class = Base.classes['r3']
            instances_r3 = sess2.query(r3_class).filter(r3_class.ur_r1_id=='21').all()
            assert len(instances_r3) == 2
