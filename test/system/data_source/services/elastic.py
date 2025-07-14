# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time

from flask import Flask

from tol.api_base import data_blueprint
from tol.core.factory import core_data_object

from .util import (
    create_indices,
    delete_indices,
    elastic_datasource,
    get_prefix,
    upsert_archetypes,
    wait_for_ready
)


wait_for_ready()


prefix = get_prefix()


# this upserts archetypes before starting, so that
# `attribute_types` and `supported_types` are
# populated
create_indices(prefix)
upsert_archetypes(prefix)
time.sleep(5)

elastic_ds = elastic_datasource(prefix)


# force the properties to have been populated
elastic_ds.supported_types
elastic_ds.attribute_types


# delete the indices and aliases
delete_indices(prefix)


core_data_object(elastic_ds)
data_bp = data_blueprint(elastic_ds)

app = Flask(__name__)
app.register_blueprint(data_bp)
