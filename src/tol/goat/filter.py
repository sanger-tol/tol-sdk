# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from ..core import DataSourceFilter


class GoatFilter(ABC):
    """
    Converts instances of `DataSourceFilter` to a
    valid GoaT filter.
    """

    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> str:
        """
        Emit a filter string from a `DataSourceFilter` instance
        """
        pass


class DefaultGoatFilter(GoatFilter):

    def __init__(
        self
    ) -> None:
        super().__init__()

    __op_mappings = {
        'eq': ['=', '!='],
        'lt': ['<', '>='],
        'lte': ['<=', '>'],
        'gt': ['>', '<='],
        'gte': ['>=', '<'],
        'contains': ['=', '!='],
        'in_list': ['=', '!='],
        'exists': ['is not null', 'is null'],
    }
    __special_fields = {
        'taxon_rank': 'tax_rank',
        'scientific_name': 'tax_name'
    }

    def dumps(self, filter_: DataSourceFilter) -> str:
        filter_conditions = []
        for field, filter_list in filter_.and_.items():
            standard_field = True
            if field == 'id':
                field = 'taxon_id'
            if field in self.__special_fields:
                field = self.__special_fields[field]
                if 'eq' in filter_list and 'value' in filter_list['eq']:
                    filter_conditions.append(f'{field}({filter_list["eq"]["value"]})')
                if 'in_list' in filter_list and 'value' in filter_list['in_list']:
                    filter_conditions.append(
                        f'{field}({",".join(filter_list["in_list"]["value"])})'
                    )
                standard_field = False
            if standard_field:
                for op, ops in self.__op_mappings.items():
                    if op in filter_list:
                        specific_filter = filter_list[op]
                        if 'value' in specific_filter:
                            operator = ops[0]
                            if 'negate' in specific_filter:
                                operator = ops[1]
                            if op == 'in_list':
                                filter_condition = ','.join(
                                    f'{v}' for v in specific_filter['value']
                                )
                            elif op == 'contains':
                                filter_condition = str(specific_filter['value']) + '*' \
                                    if 'value' in specific_filter else ''
                            else:
                                filter_condition = str(specific_filter['value']) \
                                    if 'value' in specific_filter else ''
                            filter_conditions.append(f'{field}{operator}'
                                                     f'{filter_condition}')
        filter_string = ' AND '.join(filter_conditions)
        return filter_string if filter_string is not None else ''
