# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource

EnaApiResource = dict[str, Any]
EnaApiDoc = dict[str, list[EnaApiResource]]


class Parser(ABC):
    """
    Parses ENA API transfer resource `dicts` to `DataObject`
    instances.
    """

    def parse_iterable(
        self,
        transfers: Iterable[EnaApiResource]
    ) -> Iterable[DataObject]:
        """
        Parse an `Iterable` of ENA API transfer resources.
        """
        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(
        self,
        transfer: EnaApiResource
    ) -> DataObject:
        """
        Parses an individual ENA API transfer resource to a
        `DataObject` instance.
        """


class DefaultParser(Parser):

    def __init__(
        self,
        data_source_dict: dict[str, 'DataSource']
    ) -> None:
        self.__dict = data_source_dict

    def parse(
        self,
        object_type: str,
        transfer: EnaApiResource
    ) -> DataObject:
        type_ = object_type
        ds = self.__get_data_source(type_)
        raw_attributes = transfer
        id_ = self.__get_id(type_, transfer)
        attributes = self.__convert_attributes(type_, raw_attributes)

        return ds.data_object_factory(
            type_,
            id_=id_,
            attributes=attributes,
        )

    def __get_data_source(self, type_: str) -> 'DataSource':
        if type_ not in self.__dict:
            raise ValueError(f'Data source not found for {type_}')
        return self.__dict[type_]

    def __get_id(self, type_: str, transfer: EnaApiResource) -> str:

        if type_ == 'assembly':
            return transfer['assembly_set_accession']
        elif type_ == 'read_run':
            return transfer['run_accession']
        elif type_ == 'sample':
            return transfer['sample_accession']
        elif type_ == 'study':
            return transfer['study_accession']
        elif type_ == 'taxon':
            return transfer['tax_id']

    def __convert_attributes(
        self,
        type_: str,
        attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        ret = {}
        if attributes is None:
            return ret

        for k, v in attributes.items():
            if k not in ['key'] and k in self.__dict[type_].attribute_types[type_]:
                ret[k] = v
        return ret
