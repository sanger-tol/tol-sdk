# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Flask

from tol.api_base.notification import notification_blueprint
from tol.core import DataSourceError
from tol.rabbitmq import RabbitmqConfig, create_rabbitmq_datasource

rabbitmq_ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())

app = Flask(__name__)


@app.errorhandler(DataSourceError)
def handle_ds_error(error: DataSourceError):
    """Handle data source errors and format error responses."""
    return {'errors': [{'title': error.title,
                        'detail': error.detail}]}, error.status_code


app.register_blueprint(notification_blueprint(rabbitmq_ds))
