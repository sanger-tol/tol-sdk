# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from flask import Response

from .decs import provide_body_data, provide_parameters
from ..error import BadTargetServiceException


def setup_service(cls):
    cls.setup()
    return cls


class BaseService:
    """In meta class, requires a model class, and a schema class,
    neither of which are an instantiated instance"""

    # store a registry of inherited service classes in a dict
    service_registry_dict = {}

    @classmethod
    def setup(cls):
        cls._register_service()

    @classmethod
    def _register_service(cls):
        type_ = cls.get_type()
        cls.service_registry_dict[type_] = cls

    @classmethod
    def is_enum_service(cls):
        return cls.Meta.schema.is_enum_schema()

    @classmethod
    def get_type(cls):
        return cls.Meta.schema.get_type()

    @classmethod
    def error_401(cls, message):
        return cls._custom_error(
            'Unauthorized',
            401,
            message
        )

    @classmethod
    def _custom_error(cls, title, code, detail):
        errors = [{
            'title': title,
            'code': code,
            'detail': detail
        }]
        response = {
            'errors': errors
        }
        return Response(
            mimetype='application/json',
            response=json.dumps(response),
            status=code
        )

    @classmethod
    def _get_target_service_by_name(cls, service_name):
        target_service = cls.service_registry_dict.get(service_name, None)
        if target_service is None:
            raise BadTargetServiceException(service_name)
        return target_service

    @classmethod
    def get_bulk_results_for_related_by_id(cls, id_, calling_service, parameters):
        relation_model = calling_service.get_model()
        return cls.get_model().bulk_find_on_relation_id(relation_model, id_, **parameters)

    @classmethod
    def get_bulk_results_for_related_by_name(cls, name, calling_service, parameters):
        relation_model = calling_service.get_model()
        return cls.get_model().bulk_find_on_relation_name(
            relation_model,
            name,
            **parameters
        )

    @classmethod
    def get_schema(cls, **kwargs):
        return cls.Meta.schema(**kwargs)

    @classmethod
    def get_model(cls):
        schema = cls.Meta.schema
        return schema.get_model()

    @classmethod
    def _update_model_instance(cls, old_model_instance, data, schema, user_id=None):
        new_model_instance = schema.load(
            data,
            instance=old_model_instance,
            partial=True
        )
        new_model_instance.save_update(user_id=user_id)
        return new_model_instance

    @classmethod
    def read_by_id(cls, id_, user_id=None):
        schema = cls.Meta.schema()
        model_instance = cls.Meta.model.find_by_id(id_)
        return schema.dump(model_instance), 200

    @classmethod
    @provide_body_data
    def update_by_id(cls, id_, data, user_id=None):
        schema = cls.Meta.schema()
        old_model_instance = cls.Meta.model.find_by_id(id_)
        new_model_instance = cls._update_model_instance(
            old_model_instance,
            data,
            schema,
            user_id=user_id
        )
        return schema.dump(new_model_instance), 200

    @classmethod
    def delete_by_id(cls, id_, user_id=None):
        model_instance = cls.Meta.model.find_by_id(id_)
        model_instance.delete()
        return None, 204

    @classmethod
    @provide_body_data
    def create(cls, data, user_id=None):
        schema = cls.Meta.schema()
        model_instance = schema.load(data)
        model_instance.save(user_id=user_id)
        return schema.dump(model_instance), 201

    @classmethod
    @provide_parameters
    def read_bulk(cls, paramaters, user_id=None):
        schema = cls.Meta.schema(many=True)
        model_instances, metadata = cls.Meta.model.bulk_find(**paramaters)
        response = schema.dump(model_instances)
        return dict(**metadata, **response), 200

    @classmethod
    @provide_parameters
    def read_bulk_related_by_id(cls, id_, target_service_name, parameters, user_id=None):
        """
        Called on the service for the first part of the endpoint
        e.g. A in /A/{id}/B
        """
        target_service = cls._get_target_service_by_name(target_service_name)
        schema = target_service.get_schema(many=True)
        model_instances, metadata \
            = target_service.get_bulk_results_for_related_by_id(id_, cls, parameters)
        response = schema.dump(model_instances)
        return dict(**metadata, **response), 200

    @classmethod
    def read_by_name(cls, name, user_id=None):
        """Used only for enum services"""
        schema = cls.Meta.schema()
        model_instance = cls.Meta.model.find_by_name(name)
        return schema.dump(model_instance), 200

    @classmethod
    @provide_body_data
    def update_by_name(cls, name, data, user_id=None):
        """Used only for enum services"""
        schema = cls.Meta.schema()
        old_model_instance = cls.Meta.model.find_by_name(name)
        new_model_instance = cls._update_model_instance(
            old_model_instance,
            data,
            schema,
            user_id=user_id
        )
        return schema.dump(new_model_instance), 200

    @classmethod
    def delete_by_name(cls, name, user_id=None):
        """Used only for enum services"""
        model_instance = cls.Meta.model.find_by_name(name)
        model_instance.delete()
        return None, 204

    @classmethod
    @provide_parameters
    def read_bulk_related_by_name(cls, name, target_service_name, parameters, user_id=None):
        """
        Called on the service for the first part of the endpoint
        e.g. A in /A/{name}/B

        Used only for enum services
        """
        target_service = cls._get_target_service_by_name(target_service_name)
        schema = target_service.get_schema(many=True)
        model_instances, metadata = target_service.get_bulk_results_for_related_by_name(
            name,
            cls,
            parameters
        )
        response = schema.dump(model_instances)
        return dict(**metadata, **response), 200
