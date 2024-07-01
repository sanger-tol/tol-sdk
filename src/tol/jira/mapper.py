# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


class JiraMapper():
    def __init__(
        self,
        field_mappings: dict[str, dict[str, str]]
    ) -> None:
        self.__clause_names = self._get_clause_names(field_mappings)

    def _get_clause_names(self, field_mappings: dict[str, dict[str, str]]) -> dict[str, str]:
        all_fields = {
            v['system_name']: v['clause_name']
            for v in field_mappings.values()
        }
        return all_fields | {'id': 'key'}

    def _map_field(self, field: str) -> str:
        field = field.split('.')[0]  # Remove any relation fields
        if field in self.__clause_names:
            return self.__clause_names[field]
        return field
