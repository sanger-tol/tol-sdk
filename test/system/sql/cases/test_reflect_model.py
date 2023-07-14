from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.ext.automap import automap_base
import os

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
            sess.close()

        with session_factory() as sess2:
            table = Base.classes.r1
            instance_21 = sess2.query(table).filter(table.id_override=='21').one_or_none()
            print(instance_21)
    
        assert False
