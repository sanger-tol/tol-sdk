# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from .action import Action
from ..core import DataSource


class UpsertAction(Action):
    """
    The central class for running local actions.
    """

    def __init__(self):
        super().__init__()

    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, bool], int]:

        data_objects = self.__convert_to_data_objects(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params=params
        )

        try:
            datasource.upsert_batch(object_type=object_type, objects=data_objects)
            return {'success': True}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    def __convert_to_data_objects(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> Any:
        CoreDataObject = datasource.data_object_factory # noqa N806

        for id_ in ids:
            yield CoreDataObject(
                type_=object_type,
                id_=id_,
                attributes=params
            )
