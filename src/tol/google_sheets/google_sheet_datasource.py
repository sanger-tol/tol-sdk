# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from functools import cache
from typing import Dict, Iterable, List

from dateutil.parser import parse as dateutil_parse

import gspread

from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceFilter
)
from ..core.operator import (
    DetailGetter,
    ListGetter,
)


class GoogleSheetDataSource(
    DataSource,
    DetailGetter,
    ListGetter,
):
    """
    mappings = {
        'object_name': {
            'worksheet_name': "Sheet name',
            'columns': {
                'id': {
                    'heading': 'Column name',
                    'type': 'int'
                }
                'field2': {
                    'heading': 'Column for field 2',
                    'type': 'int'
                }
            },
            'header_row': 2,
            'data_start_row': 4
        }
    }
    """

    def __init__(self, config: Dict):
        super().__init__(config, expected=[
            'client_secrets',
            'sheet_key',
            'mappings'])
        self._initialise_google_sheet()
        self.data = {}

    def _initialise_google_sheet(self):
        gc = gspread.service_account_from_dict(self.client_secrets)
        self.sheet = gc.open_by_key(self.sheet_key)

    @cache
    def _initialise_data(self, object_type):
        worksheet = self.sheet.worksheet(self.mappings[object_type]['worksheet_name'])
        self.data[object_type] = self._get_worksheet_vals(object_type, worksheet)

    def _get_header_mappings(self, object_type):
        ret = {}
        for attribute_name, metadata in self.mappings[object_type]['columns'].items():
            ret[metadata['heading']] = attribute_name
        return ret

    def __convert_type(self, object_type, header, value):
        header_mappings = self._get_header_mappings(object_type)
        target_type = self.mappings[object_type]['columns'][header_mappings[header]]['type']
        try:
            value = value.strip()
            if value == '':
                return None
            if target_type == 'int':
                return int(value)
            if target_type == 'float':
                return float(value)
        except ValueError:
            return None
        return value

    def _get_worksheet_vals(self, object_type, worksheet):
        vals = worksheet.get_values()
        header_row = self.mappings[object_type]['header_row']
        data_start_row = self.mappings[object_type]['data_start_row']
        headers = vals[header_row - 1]
        row_data = vals[data_start_row - 1:]
        ret = []
        for row in row_data:
            item = {}
            for i, header in enumerate(headers):
                if header in self._get_header_mappings(object_type).keys():
                    item[header] = self.__convert_type(object_type, header, row[i])
            ret.append(item)
        return ret

    def _convert_row_to_data_object(self, object_type, row):
        CoreDataObject = self.data_object_factory  # noqa N806
        attributes = {attribute_name: row[column_def['heading']]
                      for attribute_name, column_def
                      in self.mappings[object_type]['columns'].items()}
        # Sort out Booleans
        for attribute_name, attribute_value in attributes.items():
            if self.mappings[object_type]['columns'][attribute_name]['type'] == 'boolean' and \
                    attribute_value is not None:
                attributes[attribute_name] = True \
                    if attribute_value in [1, '1', 'Y', 'Yes', 'YES'] else False
        # Sort out datetimes
        for attribute_name, attribute_value in attributes.items():
            if self.mappings[object_type]['columns'][attribute_name]['type'] == 'datetime' and \
                    attribute_value is not None and not isinstance(attribute_value, datetime):
                dayfirst = self.mappings[object_type]['columns'][attribute_name].get(
                    'dayfirst', False
                )
                attributes[attribute_name] = dateutil_parse(
                    attribute_value,
                    dayfirst=dayfirst
                )
        return CoreDataObject(
            object_type,
            id_=attributes.pop('id', None),
            attributes=attributes
        )

    def _apply_filter(self, f: DataSourceFilter, rows: List, object_type: str):
        for row in rows:
            matches = True
            if f is not None:
                if f.in_list is not None:
                    for column_name, allowed_values in f.in_list.items():
                        key = self.mappings[object_type]['columns'][column_name]['heading']
                        if row[key] not in allowed_values:
                            matches = False
                if f.exact is not None:
                    for column_name, allowed_value in f.exact.items():
                        key = self.mappings[object_type]['columns'][column_name]['heading']
                        if row[key] != allowed_value:
                            matches = False
            if matches:
                yield row

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> Iterable[DataObject]:
        self._initialise_data(object_type)
        f = DataSourceFilter()
        f.in_list = {'id': object_ids}
        rows = self._apply_filter(f, self.data[object_type], object_type)
        for row in rows:
            yield self._convert_row_to_data_object(object_type, row)

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        self._initialise_data(object_type)
        rows = self._apply_filter(object_filters, self.data[object_type], object_type)
        for row in rows:
            obj = self._convert_row_to_data_object(object_type, row)
            if obj.id is not None:
                yield obj

    @property
    @cache
    def supported_types(self):
        return list(self.mappings.keys())

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {object_type: {attribute_name: column_def['type']
                              for attribute_name, column_def in mapping['columns'].items()}
                for object_type, mapping in self.mappings.items()}
