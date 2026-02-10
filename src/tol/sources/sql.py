# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..sql import (
    SqlDataSource,
    create_sql_datasource
)


# Create a SQL datasource. This is also expecting the models to be passed in
# so would most likely be used within an app
def sql(models, db_uri, behind_api, database_factory, **kwargs) -> SqlDataSource:
    sql_ds = create_sql_datasource(
        models=models,
        db_uri=db_uri,
        behind_api=True,
        database_factory=database_factory,
        **kwargs
    )
    core_data_object(sql_ds)
    return sql_ds
