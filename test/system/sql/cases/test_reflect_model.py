from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, relationship
import re
import os

ONLY = [
    'a',
    'b',
    'r1',
    'r2',
    'r3'
]

def test_reflect():
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

    for k,v in Base.metadata.tables.items():
        print(k)
        print(vars(v))
        print()

    assert False
