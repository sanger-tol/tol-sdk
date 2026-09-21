# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from ..action import Action
from ...core import DataSource, DataSourceError, DataSourceUtils
from ...flows.flow_utils import FlowUtils
from ...sources.benchling import benchling
from ...sources.portaldb import portaldb
from ...sources.sts import sts


class TopupAction(Action):
    """
    Performs the required topup action (e.g. tum, recollection) on the given
    objects, identified by ids and object_type.
    """

    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, bool], int]:

        if not params or 'action' not in params:
            raise DataSourceError(
                'Missing action',
                'Missing action from params',
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
        portaldb_ds = portaldb()
        data_source_instance = portaldb_ds.get_one('data_source_instance', 'tol_production')
        eds = DataSourceUtils.get_datasource_by_datasource_instance(
            data_source_instance,
            direct=True
        )
        sts_ds = sts()
        benchling_superuser = benchling()

        user_name, api_key = FlowUtils.get_user_name_and_eln_api_key(
            portaldb_ds=portaldb_ds,
            sts_ds=sts_ds,
            portal_user_id=params['user_id']
        )

        folder_name = params.get('folder_name')
        folder = FlowUtils.get_folder(bds=benchling_superuser, folder_name=folder_name)

        bds = benchling(api_key=api_key, folder_id=folder.id if folder else None)

        worklist = FlowUtils.get_worklist(
            bds=benchling_superuser,
            worklist_name=params.get('worklist_name')
        )
        print(f"Using worklist: {worklist.name if worklist else 'None'}")

        recollection_reason = params.get('recollection_reason')

        error_string = ''
        for error in FlowUtils.perform_topup_action(
            eds=eds,
            bds=bds,
            ids=ids,
            sts_ds=sts_ds,
            portaldb_ds=portaldb_ds,
            data_source_instance=data_source_instance,
            object_type=object_type,
            worklist=worklist,
            action=params['action'],
            user_id=params['user_id'],
            user_name=user_name,
            recollection_reason=recollection_reason
        ):
            error_string += f'{error}\n'

        if error_string:
            return {'error': error_string}, 500

        return {'success': True}, 200
