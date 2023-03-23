# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace, tol_fields
from tol.api_base.api.namespace import ApiNamespace
from tol.api_base.swagger.model import Swagger
from tol.api_base.utils.config import DataTypeConfig

from .data_source import _TestDataSource


INDIVIDUAL_CONFIG_DICT = {
    'object_type': 'specimen',
    'data_source': _TestDataSource({}),
    'id_field': tol_fields.Id(),
    'methods': {
        'auth': [
            'get_by_id'
        ],
        'noauth': [
            'get_list_page'
        ]
    },
    'attributes': {
        'tolid': tol_fields.String(unique=True, example='mHomSap52', required=True),
        'active': tol_fields.Boolean(required=False)
    },
    'relationships': {
        'one': {
            'species': tol_fields.ToOneRelationship(
                'species',
                'taxon_id',
                required=True,
                example='9606'
            ),
            'creator': tol_fields.ToOneRelationship(
                'users',
                'created_by',
                required=True,
                example='1',
                dump_only=True
            )
        },
        'many': {
            'samples': 'samples'
        }
    }
}


class TestApiNamespace:
    def test_resource_generation(self):
        service_ns = ServiceNamespace()

        @service_ns.route('/get-example')
        class ExampleServiceGet:
            def get(self):
                pass

        @service_ns.route('/post-example')
        class ExampleServicePost:
            def post(self):
                pass

        @service_ns.route('/delete-namespace/<str:id>')
        class ExampleServiceDeleteById:
            def delete(self, object_id):
                pass

        patch_expect_swagger = Swagger(
            'patch expect',
            {
                'test': tol_fields.String()
            }
        )

        @service_ns.route('/patch-and-get-example')
        class ExampleServicePatchAndGet:
            @service_ns.expect(
                patch_expect_swagger
            )
            def patch(self):
                pass

            def get(self):
                pass

        individual_config = DataTypeConfig(
            **INDIVIDUAL_CONFIG_DICT
        )
        api_ns = ApiNamespace(
            individual_config,
            service_ns,
            description='Test example :D'
        )

        # get the created resources
        resources = api_ns.resources
        # there should be 4
        assert len(resources) == 4

        # assert that each resource only has one url
        for resource in resources:
            assert len(resource.urls) == 1

        # make the resources dict
        resources_dict = {
            resource.urls[0]: resource.resource
            for resource in resources
        }
        print(resources_dict)
        assert False
