# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC

import dateparser

from ..datasource_filter import DataSourceFilter


class _Filterable(ABC):
    """
    Implements methods for data sources that support filtering
    e.g. ListGetter, PageGetter and Counter
    """

    def preprocess_filter(
        self,
        object_type: str,
        object_filters: DataSourceFilter
    ) -> DataSourceFilter:
        """
        The main use of this is to convert relative dates into absolute dates
        """
        for name, value in object_filters.and_.items():
            metadata = self.get_attribute_metadata_by_name(object_type, name)
            if metadata is None:
                continue
            for op, val in value.items():
                if 'value' in val and metadata['python_type'] == 'datetime':
                    object_filters.and_[name][op]['value'] = dateparser.parse(val['value'])

        return object_filters
