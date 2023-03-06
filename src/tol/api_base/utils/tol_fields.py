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


class ForeignKey(Field):
    def __init__(self, required=False, example=None):
        super().__init__(
            required=required,
            unique=False,
            example=example
        )

    @property
    def python_type(self):
        return str

    @property
    def default_example(self):
        return 'key'


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
