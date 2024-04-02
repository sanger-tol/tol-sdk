# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time
from typing import Iterable, List

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.errors import BenchlingError, WaitForTaskExpiredError
from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import (
    CustomEntityBulkUpdate
)

from caseconverter import snakecase

from more_itertools import batched

from ..core import (
    DataSource,
    DataSourceConfig,
    DataSourceError
)
from ..core.operator import Updater
from ..core.operator.updater import DataObjectUpdate

TYPE_MAPPING = {
    'text': 'str',
    'integer': 'int',
    'date': 'datetime',
    'float': 'float',
    'dropdown': 'str',
    'entity_link': 'str',
    'storage_link': 'str',
    'blob_link': 'str',
    'dna_sequence_link': 'str'
}


class BenchlingDataSource(DataSource, Updater):
    """
    A DataSource for writing objects to Benchling
    The queries are maintained in this SDK as SQL files
    """

    def __init__(self, config: DataSourceConfig) -> None:
        super().__init__(config, expected=[
            'url',
            'api_key',
            'registry_id',
            'project_id'
        ])

        self.benchling_interface = self._get_benchling_interface(self.url, self.api_key)
        self.entities = self._get_entity_schemas()

    def _get_benchling_interface(self, url, api_key):
        return (Benchling(url=url, auth_method=ApiKeyAuth(api_key)))

    def _get_entity_schemas(self):
        pages = self.benchling_interface.schemas.list_entity_schemas(
            # registry_id=self.registry_id
        )
        entities = {}
        for page in pages:
            for schema in page:
                if schema.registry_id == self.registry_id \
                        and schema.archive_record is None:
                    schema_name = snakecase(schema.name)
                    if schema_name not in entities:
                        entities[schema_name] = {}
                    for field in schema.field_definitions:
                        if field.archive_record is None:
                            entities[schema_name][snakecase(field.name)] = {
                                'name': field.name,
                                'type': TYPE_MAPPING.get(field.type.value, 'str')
                            }
        return entities

    def update(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate]
    ) -> None:
        # We have to do the updates in pages in Benchling
        for update_page in list(batched(updates, 20)):
            request = []
            error_info = {}
            for update_id, update_dict in update_page:
                entity_fields = {
                    self.entities[object_type][name]['name']: {'value': value}
                    for name, value in update_dict.items()
                }
                custom_fields = {}
                update_entity = CustomEntityBulkUpdate(
                    id=update_id,
                    fields=fields(entity_fields),
                    custom_fields=fields(custom_fields)
                )
                request.append(update_entity)
                error_info['fields'] = entity_fields
                error_info['id'] = update_id
            try:
                response = self.benchling_interface.custom_entities.bulk_update(request)
                # Try this 3 times before failing
                for i in range(3):
                    try:
                        task = self.benchling_interface.tasks.wait_for_task(
                            response.task_id, interval_wait_seconds=5)
                    except WaitForTaskExpiredError:
                        print('Time out waiting for task', flush=True)
                        if i == 2:
                            raise DataSourceError(
                                'Time out in communication with Benchling '
                                '(waiting for task response)',
                                '',
                                status_code=400)
                        time.sleep(60 * (i + 1))
                    else:
                        break
            except BenchlingError as error:
                raise DataSourceError(
                    'Error creating update task',
                    error.json['error']['message'],
                    status_code=400)
            try:
                if task.status == 'FAILED':
                    # If we are here, the batch has failed. We can try
                    # to update one-by-one
                    if len(update_page) > 1:
                        ret = []
                        for update_id, update_dict in update_page:
                            self.update(object_type, [(update_id, update_dict)])
                    else:
                        ret = [{'id': update_id, 'status': 'FAILED', 'message': task.message,
                                'errors': task.errors.to_dict(), 'update': update_page,
                                'error_info': error_info}
                               for update_id, _ in update_page]
                        print(ret, flush=True)
                else:
                    # The whole batch passed
                    pass
                    # ret = [{'id': update_id, 'status': 'PASSED'} for update_id, _ in update_page]
                    # print(ret, flush=True)
            except BenchlingError as error:
                raise DataSourceError(error.json['error']['message'], status_code=400)

    @property
    def attribute_types(self):
        return {
            k1: {
                k2: v2['type']
                for k2, v2 in v1.items()
            }
            for k1, v1 in self.entities.items()
        }

    @property
    def supported_types(self) -> List:
        return list(self.entities.keys())
