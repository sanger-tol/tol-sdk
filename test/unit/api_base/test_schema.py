# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import IdSchemes, Methods, Sources, tol_fields as fields
from tol.api_base.schema.auto import AutoSchemaGenerator
from tol.api_base.utils.config import IndividualConfig

# TODO test:
# - all declared fields are on the schema
# - datatypes are correct
# - required fields are respected
# - excluded fields are respected
# - update works correctly, with a correctly injected
#   and instantiated DataModel object
# - update is passed the ResouceMeta data


INDIVIDUAL_CONFIG = IndividualConfig(
    type_='specimen',
    meta={},
    source=Sources.DATABASE,
    id_scheme=IdSchemes.EXTERNAL,
    methods={
        'auth': [
            Methods.CREATE, Methods.DELETE, Methods.UPDATE, Methods.UPSERT
        ],
        'noauth': [
            Methods.GET, Methods.BULK_GET
        ]
    },
    attributes={
        'tolid': fields.String(unique=True, example='mHomSap52'),
        'active': fields.Boolean()
    },
    relationships={
        'one': {
            'species': 'taxon_id'
        },
        'many': [
            'samples'
        ]
    }
)


class TestAutoSchema:
    def test_all_fields_present(self):
        # generate the auto schema
        generator = AutoSchemaGenerator(INDIVIDUAL_CONFIG)
        schema_class = generator.generate()

        # assert that all fields are present
        new_fields = [
            'tolid',
            'active',
            'species',
            'samples'
        ]
        for field in new_fields:
            assert field in schema_class._declared_fields
