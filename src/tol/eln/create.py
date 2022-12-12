import json
from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.errors import BenchlingError
from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import (
    CustomEntityBulkCreate, CustomEntityBulkUpdate, CustomEntityCreate)
from benchling_api_client.models.naming_strategy import NamingStrategy

from .entities import convert_sts_entity_to_eln_entity_fields


class interface:

    def __init__(self, url, config):
        self.url = url
        api_key = config["api_key"]
        self.benchling_interface = self.__get_benchling_interface(url, api_key)
        self.registry_id = config["registry_id"]
        self.project_id = config["project_id"]
        self.mappings = config["entities"]

    def __get_benchling_interface(self, url, api_key):
        return (Benchling(url=url, auth_method=ApiKeyAuth(api_key)))

    def __generate_response(self, task, entities, id_field):
        response = [{"id": entity[id_field], "status": "PASSED"} for entity in entities]
        try:
            if task.status == "FAILED":
                print(task.message)
                for error in task.errors.additional_properties:
                    response[error["index"]]["status"] = "FAILED"
                    response[error["index"]]["message"] = error["message"]
                print(response)
                return(response)
            else:
                print("Success")
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])

    def register(self, entities, mapping_name):
        mapping = self.mappings[mapping_name]
        schema_id = mapping["schema_id"]
        id_field = mapping["id_field"]
        request = []
        for entity in entities:
            entity_fields = convert_sts_entity_to_eln_entity_fields(entity, mapping)
            name = "TEST"
            print(entity_fields)
            custom_fields = {}
            create_sample = CustomEntityBulkCreate(
                naming_strategy=NamingStrategy.IDS_FROM_NAMES,
                schema_id=schema_id,
                name=name,
                fields=fields(entity_fields),
                registry_id=self.registry_id,
                folder_id=self.project_id,
                custom_fields=fields(custom_fields))
            request.append(create_sample)
        try:
            response = self.benchling_interface.custom_entities.bulk_create(request)
            task = self.benchling_interface.tasks.wait_for_task(response.task_id, interval_wait_seconds=3)
            print(f'{response.task_id}')
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])
        return request, create_sample, self.__generate_response(task, entities, id_field)

    def update(self, entities, mapping_name):
        mapping = self.mappings[mapping_name]
        id_field = mapping["id_field"]
        request = []
        for entity in entities:
            entity_fields = convert_sts_entity_to_eln_entity_fields(entity, mapping)
            custom_fields = {}
            update_sample = CustomEntityBulkUpdate(
                # id=sample['eln_id'],
                name=entity[id_field],
                fields=fields(entity_fields),
                custom_fields=fields(custom_fields))
            request.append(update_sample)
        try:
            response = self.benchling_interface.custom_entities.bulk_update(request)
            task = self.benchling_interface.tasks.wait_for_task(
                response.task_id, interval_wait_seconds=3)
            print(f'{response.task_id}')
        except BenchlingError as error:
            raise Exception(400, error.json['error']['message'])
        return self.__generate_response(task, entities, id_field)
