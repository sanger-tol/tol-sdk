# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from ..action import Action
from ...core import DataSource, DataSourceError


class SetRelationshipAction(Action):
    """
    Sets an existing to-one relationship on one or more objects to point
    at another, already-related object, identified by its id (e.g.
    changing the species of a specimen via the species id).

    Only the relationship name is required; the type of the related
    object is looked up from the datasource's relationship config, since
    a relationship's name need not match its target type (e.g. a
    "co_author" relationship on a document may be to an "author" type).
    """

    def run(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[dict[str, bool], int]:

        if not params or 'relationship' not in params:
            raise DataSourceError(
                'Missing relationship',
                'Missing required param: "relationship"',
                400
            )

        if not params.get('related_id'):
            raise DataSourceError(
                'Missing related_id',
                'Missing required param: "related_id"',
                400
            )

        if ids is None or len(ids) == 0:
            raise DataSourceError(
                'Missing ids',
                'Missing required param: "ids"',
                400
            )

        relationship = params['relationship']
        related_id = params['related_id']
        datasource.validate_to_one_relationship(object_type, relationship)
        related_type = datasource.relationship_config[object_type].to_one[relationship]

        try:
            related_object = datasource.get_one(related_type, related_id)

            updated_objects = self.__build_updated_objects(
                datasource=datasource,
                ids=ids,
                object_type=object_type,
                relationship=relationship,
                related_object=related_object,
            )

            with datasource.get_session() as session:
                session.upsert(object_type, updated_objects)

            return {'success': True}, 200
        except Exception as e:  # noqa: BLE001
            return {'error': str(e)}, 500

    def __build_updated_objects(
        self,
        datasource: DataSource,
        ids: list[str],
        object_type: str,
        relationship: str,
        related_object: Any
    ) -> Any:

        for id_ in ids:
            parent = datasource.get_one(object_type, id_)
            setattr(parent, relationship, related_object)
            yield parent
