# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from ..core import DataSourceFilter


class EnaFilter(ABC):
    """
    Converts instances of `DataSourceFilter` to a valid ENA API query string.
    """

    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> str:
        """
        Emit a filter string from a `DataSourceFilter` instance.
        """
        pass


class DefaultEnaFilter(EnaFilter):

    def __init__(
        self,
    ) -> None:
        super().__init__()

    __op_mappings = {
        'eq': '=',
        'lt': '<',
        'lte': '<=',
        'gt': '>',
        'gte': '>=',
        'contains': ['=', '!='],
        'in_list': ['=', '!='],
        'exists': ['is not null', 'is null']
    }

    def dumps(self, filter_: DataSourceFilter) -> str:
        filter_conditions = []
        for field, filter_list in filter_.and_.items():
            standard_field = True
            if field == 'tax_eq':
                standard_field = False
            if standard_field is True:
                for op, ops in self.__op_mappings.items():
                    if op in filter_list:
                        specific_filter = filter_list[op]
                        if 'value' in specific_filter:
                            operator = ops[0]
                            if 'negate' in specific_filter:
                                operator = ops[1]
                            if op == 'in_list':
                                filter_condition = ''
                                for v in specific_filter['value']:
                                    filter_condition += f'"{v}" OR {field}='
                                filter_condition = filter_condition[:-len(field)]
                                filter_condition = filter_condition[:-4]
                                filter_condition = filter_condition.rstrip()
                            elif op == 'contains':
                                filter_condition = str(specific_filter['value']) + '*' \
                                    if 'value' in specific_filter else ''
                            else:
                                filter_condition = str(specific_filter['value']) \
                                    if 'value' in specific_filter else ''
                            filter_conditions.append(f'{field}{operator}'
                                                     f'{filter_condition}')
            else:
                for op, ops in self.__op_mappings.items():
                    if op in filter_list:
                        specific_filter = filter_list[op]
                        if op == 'in_list':
                            values = []
                            for v in specific_filter['value']:
                                values.append(f'{field}({v})')
                            filter_condition = ' OR '.join(values)
                        else:
                            val = specific_filter['value']  \
                                if 'value' in specific_filter else ''
                            filter_condition = (f'{field}({val})')
                        filter_conditions.append(filter_condition)

        filter_string = ' AND '.join(filter_conditions)
        return filter_string if filter_string is not None else ''
