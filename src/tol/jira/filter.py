# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from .mapper import JiraMapper
from ..core import DataSourceFilter


class JiraFilter(JiraMapper, ABC):
    """
    Converts instances of `DataSourceFilter` to a
    valid Jira JQL dump.
    """

    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> str:
        """
        Emit a filter string from a `DataSourceFilter` instance
        """
        pass


class DefaultJiraFilter(JiraFilter):

    def __init__(
        self,
        field_mappings: dict[str, dict[str, str]]
    ) -> None:
        super().__init__(field_mappings)

    __op_mappings = {
        'eq': ['=', '!='],
        'lt': ['<', '>='],
        'lte': ['<=', '>'],
        'gt': ['>', '<='],
        'gte': ['>=', '<'],
        'contains': ['~', '!~'],
        'in_list': ['in', 'not in'],
        'exists': ['is not null', 'is null'],
    }

    def dumps(self, filter_: DataSourceFilter) -> str:
        filter_conditions = []
        for field, filter_list in filter_.and_.items():
            for op, ops in self.__op_mappings.items():
                if op in filter_list:
                    specific_filter = filter_list[op]
                    if 'value' in specific_filter:
                        operator = ops[0]
                        if 'negate' in specific_filter:
                            operator = ops[1]
                        if op == 'in_list':
                            filter_condition = ','.join(
                                f'"{v}"' for v in specific_filter['value']
                            )
                            filter_condition = f'({filter_condition})'
                        else:
                            filter_condition = '"' + str(specific_filter['value']) + '"' \
                                if 'value' in specific_filter else ''
                        filter_conditions.append(f'{self._map_field(field)} {operator} '
                                                 f'{filter_condition}')
        filter_string = ' AND '.join(filter_conditions)
        return filter_string if filter_string is not None else ''
