# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime

import dateutil.parser

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect

from ..error import (
    BadParameterException,
    CandidateKeyNotProvidedExpection,
    EnumNameNotFoundException,
    ExtraFieldsNotPermittedException,
    IdNotFoundException,
    WildcardFilterOnNonStringColumn
)
from ..utils import (
    escape_psql_like_string,
    parse_filters,
    parse_sort_by
)


PAGE_SIZE = 20


def default_datetime_dump(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%dT%H:%M:%S.%f')
    raise TypeError()


db = SQLAlchemy(
    engine_options={
        'json_serializer': lambda obj: json.dumps(obj, default=default_datetime_dump)
    }
)


class ModelValidationError(Exception):
    def __init__(self, class_name, reason):
        super().__init__(
            f'The model class "{class_name}" failed validation due to '
            f'"{reason}".'
        )


class InstanceDoesNotExistException(IdNotFoundException):
    pass


class StemInstanceDoesNotExistException(IdNotFoundException):
    """Used on 'related' endpoints"""
    pass


class NamedEnumStemInstanceDoesNotExistException(EnumNameNotFoundException):
    """Used on 'related' endpoints concerning enum tables"""
    pass


class ExtColumn(db.Column):
    def __init__(self, **kwargs):
        super().__init__(
            db.JSON,
            nullable=False,
            default={},
            **kwargs
        )


def setup_model(cls):
    cls.setup()
    return cls


class Base(db.Model):
    """The base model class:
    - Its primary key must be called id.
    - Do not call anything other than an ExtColumn 'ext'.
    - The declared tablename will be the HTTP endpoint stem
        - It should be plural, e.g. centres
    """
    __abstract__ = True

    # a dict in which all inhertied classes are registered during setup
    model_registry_dict = {}

    # maps __tablename__ to type_
    tablename_type_dict = {}

    def __init__(self, iterable=(), **data):
        self.__dict__.update(iterable, **data)
        converted_data = self._convert_enum_names_to_foreign_key_ids(data)
        return super().__init__(**converted_data)

    @classmethod
    def _convert_enum_names_to_foreign_key_ids(cls, data):
        """Converts enum_table:name pairs into foreign_key:id pairs"""
        enum_relationship_details = cls.get_enum_relationship_details()
        enum_relation_names = [
            r_model_name for (_, r_model_name) in enum_relationship_details
        ]
        foreign_key_names = [
            fkey_name for (fkey_name, _) in enum_relationship_details
        ]
        relation_model_name_pairs = [
            (
                r_model_name,
                data.get(r_model_name, None)
            )
            for r_model_name in enum_relation_names
        ]
        enum_foreign_key_id_dict = {
            f_key_name: cls.get_model_by_type(
                r_model_name
            ).get_id_from_name(enum_name)
            for (r_model_name, enum_name), f_key_name in zip(
                relation_model_name_pairs,
                foreign_key_names
            )
            if enum_name is not None
        }
        data = {**data, **enum_foreign_key_id_dict}
        return {
            key: pair for (key, pair) in data.items()
            if key not in enum_relation_names
        }

    @classmethod
    def _convert_foreign_key_ids_to_enum_names(cls, data):
        """Converts foreign_key:id pairs into enum_table:name pairs"""
        enum_relationship_details = cls.get_enum_relationship_details()
        enum_relation_names = [
            r_model_name for (_, r_model_name) in enum_relationship_details
        ]
        foreign_key_names = [
            fkey_name for (fkey_name, _) in enum_relationship_details
        ]
        foreign_key_ids = [
            data.get(foreign_key_name, None)
            for foreign_key_name in foreign_key_names
        ]
        relation_model_name_dict = {
            r_model_name: cls.get_relation_enum_name_by_id(
                r_model_name,
                id_
            ) if id_ is not None else None
            for r_model_name, id_ in zip(
                enum_relation_names,
                foreign_key_ids,
            )
        }
        data = {**data, **relation_model_name_dict}
        return {
            key: pair for (key, pair) in data.items()
            if key not in foreign_key_names
        }

    @classmethod
    def _validate_model(cls):
        name = cls.__name__
        if not hasattr(cls, '__tablename__'):
            raise ModelValidationError(
                name,
                'No __tablename__ was declared'
            )
        if not hasattr(cls, 'Meta'):
            raise ModelValidationError(
                name,
                'No Meta class was declared'
            )
        if not hasattr(cls.Meta, 'type_'):
            raise ModelValidationError(
                name,
                'No (plural) type_ was declared on the Meta class'
            )

    @classmethod
    def setup(cls):
        cls._validate_model()
        cls._populate_target_table_dict()
        cls._register_model()

    def to_dict(self, exclude_column_names=[], convert_enums=True):
        dict_data = {
            column_name: getattr(self, column_name)
            for column_name
            in self.get_column_names()
            if column_name not in exclude_column_names
        }
        if not convert_enums:
            return dict_data
        return self._convert_foreign_key_ids_to_enum_names(dict_data)

    @classmethod
    def get_type(cls):
        return cls.Meta.type_

    @classmethod
    def _register_model(cls):
        type_ = cls.get_type()
        tablename = cls.__tablename__
        cls.model_registry_dict[type_] = cls
        cls.tablename_type_dict[tablename] = type_

    @classmethod
    def get_model_by_type(cls, type_):
        return cls.model_registry_dict[type_]

    @classmethod
    def model_is_enum(cls, type_):
        model = cls.get_model_by_type(type_)
        return model.is_enum_table()

    @classmethod
    def query(cls):
        return db.session.query(cls)

    def add(self):
        db.session.add(self)
        db.session.flush()

    def _update_ext(self, ext_data_changes):
        if not self.has_ext_column():
            raise ExtraFieldsNotPermittedException()
        ext_data = {**self.ext}
        for key, value in ext_data_changes.items():
            if value is None:
                if key in ext_data:
                    del ext_data[key]
            else:
                ext_data[key] = value
        self.ext = ext_data

    def save_update(self, **kwargs):
        if self._should_update:
            self.commit()

    def _no_change_on_columns(self, data, **kwargs):
        for key, value in data.items():
            if getattr(self, key) != value:
                return False
        return True

    def _no_change_on_ext(self, ext, **kwargs):
        for key, value in ext.items():
            if value is None and key in self.ext:
                return False
            if key not in self.ext:
                return False
            if self.ext[key] != value:
                return False
        return True

    def _no_change_on_update(self, data, ext=None, **kwargs):
        if not self._no_change_on_columns(data, **kwargs):
            return False
        if self.has_ext_column() and not self._no_change_on_ext(
            ext,
            **kwargs
        ):
            return False
        return True

    def _update_data(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def update(self, data, ext=None, **kwargs):
        converted_data = self._convert_enum_names_to_foreign_key_ids(data)
        self._should_update = True
        if self._no_change_on_update(converted_data, ext=ext, **kwargs):
            self._should_update = False
            return
        self._update_data(converted_data)
        if ext is not None:
            self._update_ext(ext)

    def delete(self):
        db.session.delete(self)
        self.commit()

    @classmethod
    def commit(cls):
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise e

    def save(self, **kwargs):
        self.add()
        self.commit()

    @classmethod
    def one_or_create(cls, candidate_key, data={}):
        """
        Returns an existing object if an instance matches ALL
        the candidate_key values, else creates a new instance
        """
        if candidate_key is None:
            raise CandidateKeyNotProvidedExpection()
        query = db.session.query(cls)
        query = cls._exact_filter_query(
            query,
            candidate_key
        ).one_or_none()
        if query is None:
            combined_data = {**data, **candidate_key}
            return cls(combined_data), True
        return query, False

    @classmethod
    def _get_exact_filter_terms(cls, exact_filters):
        if not exact_filters:
            return None
        return [
            getattr(cls, filter_key) == filter_value
            for (filter_key, filter_value)
            in cls._preprocess_exact_filters(exact_filters).items()
        ]

    @classmethod
    def _get_wildcard_filter_terms(cls, wildcard_filters):
        if not wildcard_filters:
            return None
        return [
            getattr(cls, filter_key).ilike(f'%{filter_value}%')
            for (filter_key, filter_value)
            in cls._preprocess_wildcard_filters(wildcard_filters).items()
        ]

    @classmethod
    def _get_sort_by_column(cls, sort_by_column_name, ascending):
        sort_by_column = getattr(cls, sort_by_column_name, None)
        if sort_by_column is None:
            raise BadParameterException(
                f'The field "{sort_by_column_name}" does not exist.'
            )
        return sort_by_column if ascending else sort_by_column.desc()

    @classmethod
    def _get_sort_by_non_enum(cls, query, sort_by_attribute, ascending):
        sort_by_column = cls._get_sort_by_column(
            sort_by_attribute,
            ascending
        )
        return query.order_by(sort_by_column)

    @classmethod
    def _get_sort_by_enum(cls, query, enum_name, ascending):
        enum_relation_model = cls.get_model_by_type(enum_name)
        enum_relation_tablename = enum_relation_model.__tablename__
        enum_relationship = getattr(cls, enum_relation_tablename)
        sort_by_column = enum_relation_model.name if ascending \
            else enum_relation_model.name.desc()
        return query.select_from(enum_relation_model) \
                    .join(enum_relationship) \
                    .order_by(sort_by_column)

    @classmethod
    def _sort_by_query(cls, query, sort_by):
        if sort_by is None:
            return query.order_by(cls.id)
        (sort_by_attribute, ascending) = sort_by
        if sort_by_attribute in cls._get_related_enum_table_names():
            return cls._get_sort_by_enum(
                query,
                sort_by_attribute,
                ascending
            )
        return cls._get_sort_by_non_enum(
            query,
            sort_by_attribute,
            ascending
        )

    @classmethod
    def _exact_filter_query(cls, query, exact_filters):
        exact_filter_terms = cls._get_exact_filter_terms(exact_filters)
        if exact_filter_terms is not None:
            query = query.filter(and_(*exact_filter_terms))
        return query

    @classmethod
    def _wildcard_filter_query(cls, query, wildcard_filters):
        wildcard_filters_terms = cls._get_wildcard_filter_terms(
            wildcard_filters
        )
        if wildcard_filters_terms is not None:
            query = query.filter(
                and_(*wildcard_filters_terms)
            )
        return query

    @classmethod
    def _preprocess_page(cls, page):
        if not page:
            return 1
        try:
            page = int(page)
        except ValueError:
            raise BadParameterException(
                'The page number must be an integer.'
            )
        if page < 1:
            raise BadParameterException(
                'The page number must be 1 or greater.'
            )
        return page

    @classmethod
    def _preprocess_page_size(cls, page_size):
        if not page_size:
            return PAGE_SIZE
        try:
            page_size = int(page_size)
        except ValueError:
            raise BadParameterException(
                'The page_size number must be an integer.'
            )
        if page_size < 1:
            raise BadParameterException(
                'The page_size number must be 1 or greater.'
            )
        return page_size

    @classmethod
    def _paginate_query(cls, query, page, page_size):
        page = cls._preprocess_page(page)
        page_size = cls._preprocess_page_size(page_size)
        offset = 0
        if page is not None:
            offset = (page - 1) * page_size
            query = query.offset(offset)
        return query.limit(page_size), page, page_size, offset, offset + page_size

    @classmethod
    def _postprocess_bulk_find(
        cls,
        query,
        page=None,
        page_size=None,
        filter=None,  # noqa
        sort_by=None
    ):
        exact_filters, wildcard_filters = parse_filters(filter)
        query = cls._exact_filter_query(query, exact_filters)
        query = cls._wildcard_filter_query(query, wildcard_filters)
        query = cls._sort_by_query(query, parse_sort_by(sort_by))
        total = query.count()
        query, page, page_size, offset, limit = cls._paginate_query(query, page, page_size)
        metadata = {
            'page': page,
            'page_size': page_size,
            'offset': offset,
            'limit': limit,
            'total': total
        }
        return query, metadata

    @classmethod
    def bulk_find(cls, **kwargs):
        query = db.session.query(cls)
        query, metadata = cls._postprocess_bulk_find(query, **kwargs)
        metadata = {'meta': metadata}
        return query.all(), metadata

    @classmethod
    def _bulk_find_on_relation(cls, relation_model, relation_id, **kwargs):
        foreign_key = cls._get_foreign_key_from_relation_model(relation_model)
        query = db.session.query(cls).filter(foreign_key == relation_id)
        query, metadata = cls._postprocess_bulk_find(query, **kwargs)
        metadata = {'meta': metadata}
        return query.all(), metadata

    @classmethod
    def bulk_find_on_relation_id(cls, relation_model, relation_id, **kwargs):
        cls._check_related_model_by_id_exists(relation_model, relation_id)
        return cls._bulk_find_on_relation(relation_model, relation_id, **kwargs)

    @classmethod
    def bulk_find_on_relation_name(cls, relation_model, relation_name, **kwargs):
        relation_id = cls._get_related_model_id_by_name(relation_model, relation_name)
        return cls._bulk_find_on_relation(relation_model, relation_id, **kwargs)

    @classmethod
    def _check_related_model_by_id_exists(cls, relation_model, relation_id):
        related_instance = db.session.query(relation_model) \
                                     .filter_by(id=relation_id) \
                                     .one_or_none()
        if related_instance is None:
            raise StemInstanceDoesNotExistException(
                relation_model.get_type(),
                relation_id
            )

    @classmethod
    def _get_related_model_id_by_name(cls, relation_model, relation_name):
        related_instance = db.session.query(relation_model) \
                                     .filter_by(name=relation_name) \
                                     .one_or_none()
        if related_instance is None:
            raise NamedEnumStemInstanceDoesNotExistException(
                relation_model.get_type(),
                relation_name
            )
        return related_instance.id

    @staticmethod
    def rollback():
        db.session.rollback()

    @staticmethod
    def bulk_add(data):
        db.session.add_all(data)
        db.session.commit()

    @classmethod
    def find_by_id(cls, id_):
        instance = cls.query().filter_by(id=id_).one_or_none()
        if instance is None:
            raise InstanceDoesNotExistException(
                cls.get_type(),
                id_
            )
        return instance

    @classmethod
    def _get_target_table_from_column(cls, column):
        return list(column.foreign_keys)[0].target_fullname.split('.')[0]

    @classmethod
    def _get_all_tablenames_many_to_one(cls):
        columns = cls._get_columns()
        return [
            cls._get_target_table_from_column(column)
            for column in columns
            if len(list(column.foreign_keys)) != 0
        ]

    @classmethod
    def _populate_target_table_dict(cls):
        columns = list(cls.__table__.columns)
        # this doesn't support compound/composite keys
        foreign_keys_columns = [
            c for c in columns
            if len(c.foreign_keys) == 1
        ]
        cls.target_table_column_dict = {
            cls._get_target_table_from_column(column): column
            for column
            in foreign_keys_columns
        }

    @classmethod
    def relation_is_enum(cls, type_):
        relation_model = cls.get_model_by_type(type_)
        return relation_model.is_enum_table()

    @classmethod
    def _get_foreign_key_from_relation_model(cls, relation_model):
        return cls.target_table_column_dict[relation_model.__tablename__]

    @classmethod
    def _get_columns(cls):
        return list(cls.__table__.c)

    @classmethod
    def get_nullable_column_names(cls):
        return [
            c.name for c in cls._get_columns()
            if c.nullable
        ]

    @classmethod
    def get_column_names(cls):
        return [c.name for c in cls._get_columns()]

    @classmethod
    def get_column_python_type(cls, column_name):
        column = getattr(cls, column_name)
        return column.type.python_type

    @classmethod
    def column_is_nullable(cls, column_name):
        return cls.__table__.columns[column_name].nullable

    @classmethod
    def has_ext_column(cls):
        return 'ext' in cls.get_column_names()

    @classmethod
    def has_log_details(cls):
        return False

    @classmethod
    def is_enum_table(cls):
        return False

    @classmethod
    def get_foreign_key_column_names(cls):
        return [
            c.name for c in cls._get_columns()
            if c.foreign_keys
        ]

    @classmethod
    def _get_foreign_keys_and_target_tables(cls):
        foreign_keys = cls.get_foreign_key_column_names()
        target_tablenames = [
            cls._get_target_tablename_column_from_foreign_key(c_name)[0]
            for c_name in foreign_keys
        ]
        target_table_types = [
            cls._get_type_from_tablename(tablename)
            for tablename in target_tablenames
        ]
        return foreign_keys, target_table_types

    @classmethod
    def _get_type_from_tablename(cls, tablename):
        return cls.tablename_type_dict[tablename]

    @classmethod
    def get_enum_relationship_details(cls):
        foreign_keys, target_table_types = cls._get_foreign_keys_and_target_tables()
        return [
            (column_name, target_model_type)
            for column_name, target_model_type
            in zip(foreign_keys, target_table_types)
            if cls.relation_is_enum(target_model_type)
        ]

    @classmethod
    def get_target_table_type_column_from_foreign_key(cls, foreign_key_name):
        target_table, target_column = cls._get_target_tablename_column_from_foreign_key(
            foreign_key_name
        )
        target_table_type = cls._get_type_from_tablename(target_table)
        return target_table_type, target_column

    @classmethod
    def get_related_enum_types(cls):
        return [
            target_table_type for (_, target_table_type)
            in cls.get_enum_relationship_details()
        ]

    @classmethod
    def get_relation_id_by_enum_name(cls, relation_type, enum_name):
        relation_model = cls.get_model_by_type(relation_type)
        return relation_model.get_id_from_name(enum_name)

    @classmethod
    def get_relation_enum_name_by_id(cls, relation_type, id_):
        relation_model = cls.get_model_by_type(relation_type)
        return relation_model.get_name_from_id(id_)

    @classmethod
    def _get_related_enum_table_names(cls):
        _, target_tables = cls._get_foreign_keys_and_target_tables()
        return [
            t_table for t_table in target_tables
            if cls.relation_is_enum(t_table)
        ]

    @classmethod
    def get_one_to_many_relationship_names(cls):
        relationships = inspect(cls).relationships.items()
        relationship_names = [r[0] for r in relationships]
        # exclude relationships for which this model is the many end
        return [
            cls._get_type_from_tablename(r) for r in relationship_names
            if r not in cls._get_all_tablenames_many_to_one()
        ]

    @classmethod
    def _get_target_tablename_column_from_foreign_key(cls, column_name):
        """Returns a pair:
        - The target table's name
        - The name of the target column on the target table
        """
        # TODO make this support composite/compound keys
        foreign_key = list(cls.__table__.columns[column_name].foreign_keys)[0]
        target_table, target_column = foreign_key.target_fullname.split('.')
        return target_table, target_column

    @classmethod
    def _filter_value_is_float(cls, filter_value):
        try:
            float(filter_value)
            return True
        except ValueError:
            return False

    @classmethod
    def _filter_value_is_datetime(cls, filter_value):
        try:
            dateutil.parser.parse(filter_value)
            return True
        except ValueError:
            return False

    @classmethod
    def _filter_value_is_bool(cls, filter_value):
        return filter_value.lower() in ['true', 'false']

    @classmethod
    def _preprocess_non_string_filter_value(cls, filter_value, python_type):
        if python_type == int and not filter_value.isdigit():
            raise BadParameterException(
                f"The filter value '{filter_value}' must be an integer."
            )
        if python_type == float and not cls._filter_value_is_float(filter_value):
            raise BadParameterException(
                f"The filter value '{filter_value}' must be a float (number)."
            )
        if python_type == datetime and not cls._filter_value_is_datetime(filter_value):
            raise BadParameterException(
                f"The filter value '{filter_value}' must be a valid datetime."
            )
        if python_type == bool:
            if not cls._filter_value_is_bool(filter_value):
                raise BadParameterException(
                    f"The filter value '{filter_value}' must be a boolean"
                )
            # convert to boolean
            return filter_value.lower() == 'true'
        # nothing needs to change, return unmodified filter value
        return filter_value

    @classmethod
    def _preprocess_enum_filter(cls, filter_key, filter_enum_name):
        enum_relation_model = cls.get_model_by_type(filter_key)
        valid_enum_names = enum_relation_model.get_enum_values()
        if filter_enum_name not in valid_enum_names:
            raise BadParameterException(
                f"The (filter) name '{filter_enum_name}' does not exist on "
                f'the enum {filter_key}.'
            )
        return filter_enum_name

    @classmethod
    def _preprocess_exact_filter_value(cls, filter_key, filter_value, enum_names):
        if getattr(cls, filter_key, None) is None and filter_key not in enum_names:
            raise BadParameterException(
                f"The filter key '{filter_key}' is invalid."
            )
        # pre-remove enum types
        if filter_key in enum_names:
            return cls._preprocess_enum_filter(filter_key, filter_value)
        return filter_value

    @classmethod
    def _preprocess_wildcard_filter_value(cls, filter_key, filter_value):
        python_type = cls.get_column_python_type(filter_key)

        if python_type != str:
            raise WildcardFilterOnNonStringColumn(filter_key)

        return escape_psql_like_string(filter_value)

    @classmethod
    def _check_not_ext_filter(cls, filters):
        if cls.has_ext_column() and 'ext' in filters.keys():
            raise BadParameterException(
                "This API cannot filter against 'extra' columns."
            )

    @classmethod
    def _preprocess_exact_filters(cls, exact_filters):
        if not exact_filters:
            return None
        cls._check_not_ext_filter(exact_filters)
        enum_names = cls.get_related_enum_types()
        processed_exact_filters = {
            filter_key: cls._preprocess_exact_filter_value(
                filter_key,
                filter_value,
                enum_names
            )
            for (filter_key, filter_value)
            in exact_filters.items()
        }
        return cls._convert_enum_names_to_foreign_key_ids(
            processed_exact_filters
        )

    @classmethod
    def _preprocess_wildcard_filters(cls, wildcard_filters):
        if not wildcard_filters:
            return None
        cls._check_not_ext_filter(wildcard_filters)
        return {
            filter_key: cls._preprocess_wildcard_filter_value(
                filter_key,
                filter_value
            )
            for (filter_key, filter_value)
            in wildcard_filters.items()
        }
