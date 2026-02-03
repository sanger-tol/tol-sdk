# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from ..core import DataObject, DataSourceParser


ElasticApiResource = dict[str, Any]


class DefaultParser(DataSourceParser[ElasticApiResource]):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    # def parse(self, transfer: ElasticApiResource) -> DataObject:
    #     if '_source' in transfer:
    #         type_ = self.__real_index_to_object_type(transfer['_index'])  # TODO IN DATA SOURCE
    #         id_ = transfer['_id']
    #         attributes = transfer['_source']
    #         runtime_attributes = transfer['fields'] if 'fields' in transfer else {}
    #         return self._convert_data_dict_to_data_object(
    #             type_,
    #             id_,
    #             attributes,
    #             runtime_attributes
    #         )
    #     else:
    #         return None
    
    # def _convert_data_dict_to_data_object(self, type_, id_, data, runtime_data):
    #     attributes = {
    #         k: self.__make_dates(type_, k, v) for k, v in data.items()
    #         if k in self.attribute_types[type_]
    #     }
    #     # make_dates might shift to parser (&make_to_one_relations?)
    #     # get real index stay in ds
    #     runtime_attributes = {
    #         k: self.__make_dates(type_, k, v[0]) for k, v in runtime_data.items()
    #         if k in self.attribute_types[type_]
    #     }
    #     to_one = self.__make_to_one_relations(type_, data)
    #     return self.data_object_factory(
    #         type_,
    #         id_=id_,
    #         attributes=attributes | runtime_attributes,
    #         to_one=to_one
    #     )
