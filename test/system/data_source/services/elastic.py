# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time

from flask import Flask

from tol.api_base import data_blueprint
from tol.core.factory import core_data_object

from .util import (
    create_indices,
    elastic_datasource,
    upsert_archetypes,
    wait_for_ready
)


wait_for_ready()


# this upserts archetypes before starting, so that
# `attribute_types` and `supported_types` are
# populated
create_indices()
upsert_archetypes()
time.sleep(5)

elastic_ds = elastic_datasource()
core_data_object(elastic_ds)
data_bp = data_blueprint(elastic_ds)

app = Flask(__name__)
app.register_blueprint(data_bp)
