# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from flask import Blueprint, Response

from marshmallow.exceptions import (
    MarshmallowError,
    ValidationError
)

from marshmallow_jsonapi.exceptions import IncorrectTypeError

from sqlalchemy.exc import IntegrityError

from .error import _CustomException


blueprint = Blueprint('error_handler', __name__)


@blueprint.app_errorhandler(_CustomException)
def handle_custom_exception(error: _CustomException):
    return Response(
        mimetype='application/json',
        response=json.dumps(error.to_dict()),
        status=error.status_code
    )


@blueprint.app_errorhandler(IntegrityError)
def handle_integrity_error(_error: IntegrityError):
    message = (
        'An integrity error occured in the database. '
        'This is most likely due to either a dependency on '
        'this instance, if deleting, or a foreign reference '
        'to an object that does not exist, if creating/updating.'
    )
    errors = [{
        'title': 'Integrity Error',
        'detail': message
    }]
    return Response(
        mimetype='application/json',
        response=json.dumps({
            'errors': errors
        }),
        status=400
    )


@blueprint.app_errorhandler(ValidationError)
@blueprint.app_errorhandler(IncorrectTypeError)
def handle_validation_error(error: MarshmallowError):
    return Response(
        mimetype='application/json',
        response=json.dumps(error.messages),
        status=400
    )
