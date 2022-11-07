import json

from typing import List
from flask import Blueprint, Response


error_handler_blueprint = Blueprint('error_handler', __name__)


class CustomException(Exception):
    def __init__(self, errors: List, status_code: int=500):
        self.errors = errors
        self.status_code = status_code


@error_handler_blueprint.app_errorhandler(CustomException)
def handle_custom_exception(exception: CustomException):
    data = {
        'errors': exception.errors
    }
    return Response(
        mimetype="application/json",
        response=json.dumps(data),
        status=exception.status_code
    )
