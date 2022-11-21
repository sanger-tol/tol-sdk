# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_restx import Resource

from ..service import EnvironmentService
from ..swagger import EnvironmentSwagger


api_environment = EnvironmentSwagger.api


@api_environment.route('')
class EnvironmentResource(Resource):
    @api_environment.doc('Gets the deployment environment string')
    @api_environment.response(
        200,
        description='Success',
        model=EnvironmentSwagger.response_model,
    )
    def get(self):
        return EnvironmentService.get_environment()
