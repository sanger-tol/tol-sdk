# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable, Iterator

from . import DataSourceError, OperableDataSource
from .operator import Relational
from .relationship import RelationshipConfig


class ReqFieldsTree:
    """
    Acts as a template for which related objects and attributes to fetch from
    the DataSource, and for serialzing them in the response.
    """

    def __init__(
        self,
        object_type: str,
        data_source: OperableDataSource,
        requested_fields: list[str] | None = None,
        include_all_to_ones: bool = True,
    ) -> None:
        self.__object_type: str = object_type
        self.__attributes: dict[str, bool] = {}
        self.__sub_trees: dict[str, ReqFieldsTree] = {}
        self.__rel_conf: RelationshipConfig | None = (
            data_source.relationship_config.get(object_type)
            if isinstance(data_source, Relational)
            else None
        )
        if requested_fields:
            self.add_requested_tree(data_source, requested_fields)
        elif include_all_to_ones:
            self.add_all_to_ones(data_source)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @property
    def object_type(self) -> str:
        return self.__object_type

    @property
    def attribute_names(self) -> list[str]:
        return list(self.__attributes)

    def add_attribute(self, name: str) -> None:
        """
        Add attribute `name`. Attributes are implemented as a dict rather than
        a set to preserve order.
        """
        self.__attributes[name] = True

    def has_attribute(self, name: str) -> bool:
        return name in self.__attributes

    def add_sub_tree(self, name: str, sub: ReqFieldsTree) -> None:
        self.__sub_trees[name] = sub

    def get_sub_tree(self, name: str) -> ReqFieldsTree | None:
        return self.__sub_trees.get(name)

    def sub_trees(self) -> Iterator[str, ReqFieldsTree]:
        """
        Iterator over `name, sub_tree`.
        """
        yield from self.__sub_trees.items()

    @property
    def is_leaf(self) -> bool:
        """
        This tree is a leaf if it has no sub-trees.
        """
        return not self.__sub_trees

    @property
    def is_stub(self) -> bool:
        """
        This tree is a stub if it has no sub-trees and has one attribute which
        is "id".
        """
        if self.__sub_trees:
            return False
        return len(self.__attributes) == 1 and 'id' in self.__attributes

    @property
    def has_relationships(self) -> bool:
        return self.__rel_conf is not None

    def to_one_names(self) -> Iterable[str]:
        return x.keys() if (x := self.__rel_conf.to_one) else ()

    def to_many_names(self) -> Iterable[str]:
        return x.keys() if (x := self.__rel_conf.to_many) else ()

    def get_relationship(self, name: str) -> str:
        """
        Fetches the related object type from the `to_one` or `to_many` fields
        of the attached `RelationshipConfig`.
        """
        if rel_conf := self.__rel_conf:
            for attr in 'to_one', 'to_many':
                if (cfg := getattr(rel_conf, attr)) and (type_name := cfg.get(name)):
                    return type_name

    def get_attribute_type(self, data_source, name) -> type | None:
        return data_source.attribute_types[self.object_type].get(name)

    def add_all_to_ones(self, data_source: OperableDataSource) -> None:
        if not self.__rel_conf:
            return
        for name in self.to_one_names():
            sub_type = self.get_relationship(name)
            self.add_sub_tree(
                name,
                self.__class__(
                    sub_type,
                    data_source,
                    include_all_to_ones=False,
                ),
            )

    def add_requested_tree(
        self,
        data_source: OperableDataSource,
        requested_fields: list[str],
    ) -> None:
        err_title = 'Bad Requested Fields Path Element'
        for path_str in requested_fields:
            tree = self
            for name in path_str.split('.'):
                if name == '':
                    msg = f"Empty element in path path '{path_str}'"
                    raise DataSourceError(title=err_title, detail=msg)
                elif not tree:
                    msg = f"Element '{name}' appears after an attribute name in path '{path_str}'"
                    raise DataSourceError(title=err_title, detail=msg)
                elif sub_tree := tree.get_sub_tree(name):
                    # `name` is a relationship we already have so move pointer
                    # to the sub tree.
                    tree = sub_tree
                elif tree.has_attribute(name):
                    # Already have attribute `name`. Unset `tree` to trap path
                    # elements follwing an attribute.
                    tree = None
                elif sub_type := tree.get_relationship(name):
                    # New sub-tree from relationship name.
                    sub_tree = self.__class__(
                        sub_type,
                        data_source,
                        include_all_to_ones=False,
                    )
                    tree.add_sub_tree(name, sub_tree)
                    tree = sub_tree
                elif tree.get_attribute_type(data_source, name):
                    tree.add_attribute(name)
                    # Unset `tree` to trap path elements follwing an
                    # attribute.
                    tree = None
                else:
                    msg = (
                        f'{name!r} in path {path_str!r} is not a known relationship'
                        f' or attribute of {tree.object_type!r} objects'
                    )
                    raise DataSourceError(title=err_title, detail=msg)

    def __str__(self):
        return ','.join(self.__to_strings_iter())

    def to_paths(self) -> list[str]:
        return list(self.__to_strings_iter())

    def __to_strings_iter(self, *path: list[str]) -> Iterator[str]:
        for name in self.__attributes:
            yield '.'.join([*path, name])
        if self.is_leaf:
            # We only need to return the path to self if it hasn't already
            # appeared as a root path under an attribtue.
            if path and not self.__attributes:
                yield '.'.join(path)
        else:
            for name, tree in self.sub_trees():
                yield from tree.__to_strings_iter(*path, name)
