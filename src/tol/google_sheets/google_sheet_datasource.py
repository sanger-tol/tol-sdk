# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from functools import cache
from typing import Dict, Iterable, List

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
        gc = gspread.service_account_from_dict(json.loads(self.client_secrets))
        self.sheet = gc.open_by_key(self.sheet_key)

    def _initialise_data(self, object_type):
        worksheet = self.sheet.worksheet(self.mappings[object_type]['worksheet_name'])
        self.data[object_type] = worksheet.get_all_records(
            head=self.mappings[object_type]['header_row'],
            default_blank=None
        )
        # We need to delete all the rows that are before the 'data_start_row'
        row_to_start_from = self.mappings[object_type]['data_start_row'] - \
            self.mappings[object_type]['header_row'] - 1
        self.data[object_type] = self.data[object_type][row_to_start_from:]

    def _convert_row_to_data_object(self, object_type, row):
        CoreDataObject = self.data_object_factory  # noqa N806
        attributes = {attribute_name: row[column_def['heading']]
                      for attribute_name, column_def
                      in self.mappings[object_type]['columns'].items()}
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
            yield self._convert_row_to_data_object(object_type, row)

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
