# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractproperty


class Field(ABC):
    """
    The base class for all config field types. Should
    not be used directly.
    """

    def __init__(
        self,
        required=False,
        unique=False,
        example=None
    ):
        self.__required = required
        self.__unique = unique
        self.__example = example

    @property
    def required(self):
        return self.__required

    @property
    def unique(self):
        return self.__unique

    @property
    def example(self):
        return (
            self.__example
            if self.__example is not None
            else self.default_example
        )

    @abstractproperty
    def python_type(self):
        pass

    @abstractproperty
    def default_example(self):
        pass


class Id(Field):
    """
    The ID field of an archetype.
    """
    def __init__(
        self,
        example=None,
        dump_only=False
    ):
        self.__dump_only = dump_only
        super().__init__(
            required=True,
            unique=True,
            example=example
        )

    @property
    def python_type(self):
        return str

    @property
    def default_example(self):
        return 'example-ID'

    @property
    def dump_only(self):
        return self.__dump_only


class ToOneRelationship(Field):
    """
    This creates a -to-one relationship towards the target.
    """
    def __init__(
        self,
        target: str,
        foreign_key: str,
        required=False,
        example=None,
        dump_only=False
    ):
        self.__target = target
        self.__dump_only = dump_only
        self.__foreign_key = foreign_key
        super().__init__(
            required=required,
            unique=False,
            example=example
        )

    @property
    def foreign_key(self):
        return self.__foreign_key

    @property
    def target(self):
        return self.__target

    @property
    def python_type(self):
        return str

    @property
    def default_example(self):
        return 'key'

    @property
    def dump_only(self):
        return self.__dump_only


class String(Field):
    @property
    def python_type(self):
        return str

    @property
    def default_example(self):
        return 'string'


class Integer(Field):
    @property
    def python_type(self):
        return int

    @property
    def default_example(self):
        return 1


class Boolean(Field):
    @property
    def python_type(self):
        return bool

    @property
    def default_example(self):
        return True
