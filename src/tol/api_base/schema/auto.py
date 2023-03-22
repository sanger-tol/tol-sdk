# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Dict

from marshmallow_jsonapi import Schema, fields as schema_fields

from ..utils import tol_fields
from ..utils.config import DataTypeConfig


class AutoSchemaGenerator:
    """
    Generates an AutoSchema class, given the
    config for an individual type. Consider
    this a private API!
    """

    def __init__(self, config: DataTypeConfig):
        self.__config = config
        self.__extra_attributes: Dict[str, schema_fields.Field] = {}

    def generate(self):
        self.__generate_extra_attributes()
        return self.__generate_new_schema_class()

    def __generate_extra_attributes(self):
        self.__generate_id()
        self.__generate_regular_attributes()
        self.__generate_one_relationships()
        self.__generate_many_relationships()
        self.__generate_meta_class()

    def __generate_regular_attributes(self) -> None:
        for attribute, tol_field in self.__config.attributes.items():
            schema_field = self.__generate_schema_field_from_tol_field(
                tol_field
            )
            self.__extra_attributes[attribute] = schema_field

    def __generate_schema_field_from_tol_field(
        self,
        tol_field: tol_fields.Field
    ) -> schema_fields.Field:
        schema_field_class = self.__get_schema_field_from_python_type(
            tol_field.python_type
        )
        return schema_field_class(
            required=tol_field.required
        )

    def __generate_one_relationship_field(
        self,
        relationship: tol_fields.ToOneRelationship
    ) -> schema_fields.Relationship:

        target = relationship.target
        foreign_key_name = relationship.foreign_key
        return schema_fields.Relationship(
            related_url=f'/{target}/{{id}}',
            related_url_kwargs={'id': f'<{foreign_key_name}>'},
            include_resource_linkage=True,
            type_=target,
            attribute=foreign_key_name,
            dump_only=relationship.dump_only,
            required=relationship.required
        )

    def __get_schema_field_from_python_type(
        self,
        python_type: object
    ) -> schema_fields.Field:
        if python_type == str:
            return schema_fields.String
        if python_type == int:
            return schema_fields.Integer
        if python_type == bool:
            return schema_fields.Boolean
        if python_type == datetime:
            return schema_fields.DateTime
        raise NotImplementedError()

    def __generate_one_relationships(self) -> None:
        one = self.__config.relationships.one
        for field_name, config in one.items():
            field = self.__generate_one_relationship_field(
                config
            )
            self.__extra_attributes[field_name] = field

    def __generate_many_relationships(self) -> None:
        for field_name, target in self.__config.relationships.many.items():
            field = self.__generate_many_relationship_for_target(
                target
            )
            self.__extra_attributes[field_name] = field

    def __generate_many_relationship_for_target(
        self,
        target: str
    ) -> schema_fields.Relationship:

        type_ = self.__config.object_type
        return schema_fields.Relationship(
            f'/{type_}/{{id}}/{target}',
            related_url_kwargs={'id': '<id>'},
            many=True,
            type_=target,
            dump_default=lambda: []
        )

    def __generate_meta_class(self) -> None:
        stored_type = self.__config.object_type

        class Meta:
            type_ = stored_type
        self.__extra_attributes['Meta'] = Meta

    def __generate_id(self) -> None:
        id_field = self.__generate_id_field(
            self.__config.id_field
        )
        self.__extra_attributes['id'] = id_field

    def __generate_id_field(
        self,
        id_from_archetype: tol_fields.Id
    ) -> schema_fields.Field:
        return schema_fields.String(
            required=True,
            dump_only=id_from_archetype.dump_only
        )

    def __generate_new_schema_class(self) -> Schema:
        name = f'{self.__config.object_type.capitalize()}Schema'
        return type(
            name,
            (Schema,),
            self.__extra_attributes
        )
