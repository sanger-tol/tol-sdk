# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..core import DataSourceFilter


class GoatFilter(ABC):
    """
    Converts instances of `DataSourceFilter` to
    valid GoaT query components.
    """

    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> Dict[str, Any]:
        """
        Emit a `dict` of GoaT query components (such as
        `attributes`, `taxa` and `rank`) from a
        `DataSourceFilter` instance
        """
        pass


class DefaultGoatFilter(GoatFilter):

    def __init__(
        self
    ) -> None:
        super().__init__()

    __op_mappings = {
        'eq': ['eq', 'ne'],
        'lt': ['lt', 'ge'],
        'lte': ['le', 'gt'],
        'gt': ['gt', 'le'],
        'gte': ['ge', 'lt'],
        'contains': ['eq', 'ne'],
        'in_list': ['eq', 'ne'],
        'exists': ['exists', 'missing'],
    }
    # These are filtered as taxon names/IDs rather than attributes
    __taxa_fields = ['taxon_id', 'scientific_name']

    def dumps(self, filter_: DataSourceFilter) -> Dict[str, Any]:
        attributes = []
        taxa = []
        rank = None
        if filter_ is None or filter_.and_ is None:
            return {}
        for field, filter_list in filter_.and_.items():
            if field == 'id':
                field = 'taxon_id'
            if field in self.__taxa_fields:
                if 'eq' in filter_list and 'value' in filter_list['eq']:
                    taxa.append(str(filter_list['eq']['value']))
                if 'in_list' in filter_list and 'value' in filter_list['in_list']:
                    taxa.extend(
                        str(v) for v in filter_list['in_list']['value']
                    )
                if field == 'scientific_name' and \
                        'contains' in filter_list and \
                        'value' in filter_list['contains']:
                    taxa.append(f'*{filter_list["contains"]["value"]}*')
                continue
            if field == 'taxon_rank':
                if 'eq' in filter_list and 'value' in filter_list['eq']:
                    rank = str(filter_list['eq']['value'])
                continue
            for op, ops in self.__op_mappings.items():
                if op not in filter_list:
                    continue
                specific_filter = filter_list[op]
                operator = ops[1] if 'negate' in specific_filter else ops[0]
                attribute = {'name': field, 'operator': operator}
                if op == 'exists':
                    # exists/missing take no value
                    attributes.append(attribute)
                    continue
                if 'value' not in specific_filter:
                    continue
                if op == 'contains':
                    attribute['value'] = f'{specific_filter["value"]}*'
                elif op == 'in_list':
                    attribute['value'] = [
                        str(v) for v in specific_filter['value']
                    ]
                else:
                    attribute['value'] = str(specific_filter['value'])
                attributes.append(attribute)
        query = {}
        if attributes:
            query['attributes'] = attributes
        if taxa:
            query['taxa'] = taxa
        if rank is not None:
            query['rank'] = rank
        return query
