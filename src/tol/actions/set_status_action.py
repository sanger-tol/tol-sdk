# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .action import Action
from ..core import DataSource, DataSourceError


class SetStatusAction(Action):
    """
    Sets the status of one or more objects by inserting a new row into
    the corresponding status history table.
    """

    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, bool], int]:

        if not params or 'status' not in params:
            raise DataSourceError(
                'Missing status',
                'Missing status from params',
                400
            )

        if ids is None or len(ids) == 0:
            raise DataSourceError(
                'Missing ids',
                'Missing required param: "ids"',
                400
            )

        if 'user_id' not in params:
            raise DataSourceError(
                'Missing user_id',
                'Missing required param: "user_id"',
                400
            )

        user_id = params['user_id'] if 'user_id' in params else None
        status_type_id = params['status']
        status_table = f'{object_type}_status'
        status_type_table = f'{object_type}_status_type'

        try:
            status_type = datasource.get_one(status_type_table, status_type_id)

            new_status_objects = self.__build_status_objects(
                datasource=datasource,
                ids=ids,
                object_type=object_type,
                status_table=status_table,
                status_type=status_type,
                user_id=user_id,
            )

            with datasource.get_session() as session:
                for obj in session.insert(status_table, new_status_objects):
                    parent = obj.to_one_relationships.get(object_type)
                    setattr(parent, 'status', obj)
                    session.upsert(object_type, [parent])

            return {'success': True}, 200
        except Exception as e:  # noqa: BLE001
            return {'error': str(e)}, 500

    def __build_status_objects(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        status_table: str,
        status_type: Any,
        user_id: str | None = None
    ) -> Any:

        for id_ in ids:
            parent = datasource.get_one(object_type, id_)
            yield datasource.data_object_factory(
                type_=status_table,
                attributes={
                    'status_time': datetime.now(tz=timezone.utc),
                    'modified_at': datetime.now(tz=timezone.utc),
                    'modified_by': user_id,
                },
                to_one={
                    object_type: parent,
                    'status_type': status_type,
                },
            )
