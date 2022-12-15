# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from benchling_api_client.models.naming_strategy import NamingStrategy

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.errors import BenchlingError
from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import (
    CustomEntityBulkCreate, CustomEntityBulkUpdate)

from .entities import convert_sts_entity_to_eln_entity_fields


class Interface:

    def __init__(self, config, api_key='DEFAULT'):
        if api_key == 'DEFAULT':
            self.api_key = config['api_key']
        else:
            self.api_key = api_key
        self.url = config['url']
        self.registry_id = config['registry_id']
        self.project_id = config['project_id']
        self.mappings = config['entities']
        self.benchling_interface = self.__get_benchling_interface(self.url, self.api_key)

    def __get_benchling_interface(self, url, api_key):
        return (Benchling(url=url, auth_method=ApiKeyAuth(api_key)))

    def __generate_response(self, task, entities, id_field):
        response = [{'id': entity[id_field], 'status': 'PASSED'} for entity in entities]
        try:
            if task.status == 'FAILED':
                for error in task.errors.additional_properties:
                    response[error['index']]['status'] = 'FAILED'
                    response[error['index']]['message'] = error['message']
                return response
            else:
                return response
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])

    def register(self, entities, mapping_name):
        mapping = self.mappings[mapping_name]
        schema_id = mapping['schema_id']
        name_field = mapping['name_field']
        request = []
        for entity in entities:
            entity_fields = convert_sts_entity_to_eln_entity_fields(entity, mapping)
            print(json.dumps(entity_fields, indent=4))
            name = entity[name_field]
            custom_fields = {}
            create_sample = CustomEntityBulkCreate(
                naming_strategy=NamingStrategy.REPLACE_NAMES_FROM_PARTS,
                schema_id=schema_id,
                name=name,
                fields=fields(entity_fields),
                folder_id=self.project_id,
                registry_id=self.registry_id,
                custom_fields=fields(custom_fields))
            request.append(create_sample)
        try:
            response = self.benchling_interface.custom_entities.bulk_create(request)
            task = self.benchling_interface.tasks.wait_for_task(
                response.task_id, interval_wait_seconds=3)
            print(f'{response.task_id}')
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])
        response = [{'name': entity[name_field], 'status': 'PASSED'} for entity in entities]
        try:
            if task.status == 'FAILED':
                for error in task.errors.additional_properties:
                    response[error['index']]['status'] = 'FAILED'
                    response[error['index']]['message'] = error['message']
                return response
            else:
                return response
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])

    def update(self, entities, mapping_name):
        mapping = self.mappings[mapping_name]
        id_field = mapping['id_field']
        request = []
        for entity in entities:
            entity_fields = convert_sts_entity_to_eln_entity_fields(entity, mapping)
            custom_fields = {}
            update_sample = CustomEntityBulkUpdate(
                id=entity[id_field],
                fields=fields(entity_fields),
                custom_fields=fields(custom_fields))
            request.append(update_sample)
        try:
            response = self.benchling_interface.custom_entities.bulk_update(request)
            task = self.benchling_interface.tasks.wait_for_task(
                response.task_id, interval_wait_seconds=3)
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])
        response = [{'id': entity[id_field], 'status': 'PASSED'} for entity in entities]
        try:
            if task.status == 'FAILED':
                response = [{'id': entity[id_field],
                             'status': 'FAILED',
                             'message': task.message} for entity in entities]
            return response
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])
