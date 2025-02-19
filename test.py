# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from minio import Minio
import json
from io import BytesIO

from tol.gap import GapDataSource

from tol.core import (
    core_data_object
)

from dotenv import load_dotenv

load_dotenv('/Users/lh31/projects/tol-sdk/.env.dev')


# MinIO Configuration
s3_endpoint = "cog.sanger.ac.uk"
s3_access_key="newaccesskey"
s3_secret_key="newsecretkey"
s3_bucket="test-bucket"
s3_object="data.json"




config = {
    "type": "object1",
    "id_attribute": "Id",
    "uri": f"s3://tol-system-test-assets/test.json",
    "s3_access_key": 'MD8EDMSNP9M8D87C7AU4',
    "s3_secret_key": 'ADdE4mPDqlMd2jolZjaQI0tt8CV2RaeAZWU2Rkgv',
    "s3_host": s3_endpoint,
    'mappings': {
            'id': {
                'heading': 'Id',
                'type': 'int'
            },
            'value': {
                'heading': 'Value',
                'type': 'str'
            },
            'optional': {
                'heading': 'Optional',
                'type': 'str'
            },
            'boolean': {
                'heading': 'Boolean',
                'type': 'boolean'
            },
            'float': {
                'heading': 'Float',
                'type': 'float'
            },
            'datetime': {
                'heading': 'Datetime',
                'type': 'datetime'
            }
        }
}


ds = GapDataSource(
    config,
    secure=True,
)

cdo = core_data_object(ds)

# Use ds as normal
objs = ds.get_by_id('object1', [1, 4])

print(next(objs).id)

objs = ds.get_to_many_relations(next(objs))
