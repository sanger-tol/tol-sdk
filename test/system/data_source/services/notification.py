# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Flask

from tol.api_base import data_blueprint
from tol.rabbitmq import RabbitmqConfig, create_rabbitmq_datasource

rabbitmq_ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())

app = Flask(__name__)
app.register_blueprint(data_blueprint(rabbitmq_ds))
