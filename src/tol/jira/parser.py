# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from dateutil.parser import parse as dateutil_parse

from ..core import DataObject, DataSource

JiraTransfer = dict[str, Any]


class Parser(ABC):
    """
    Parses Jira issue `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[JiraTransfer]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of Jira issues
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: JiraTransfer) -> DataObject:
        """
        Parses an individual Jira issue to a
        `DataObject` instance
        """


class DefaultParser(Parser):
    """
    A trivial implementation of `Parser` that is not intended to be used
    """
    def __init__(
        self,
        data_source_dict: dict[str, DataSource],
        field_mappings: dict[str, dict[str, str]]
    ) -> None:
        self.__dict = data_source_dict
        self.__field_mappings = field_mappings

    __IGNORE_FIELDS = ['attachment', 'comment', 'customfield_10000',
                       'worklog', 'votes', 'watches']

    def parse(self, transfer: JiraTransfer) -> DataObject:
        if 'fields' in transfer:
            return self.__parse_issue(transfer)
        elif 'emailAddress' in transfer:
            return self.__parse_user(transfer)
        elif 'from' in transfer:
            return self.__parse_issue_status_changelog(transfer)

    def __parse_issue(self, transfer: JiraTransfer) -> DataObject:
        type_ = 'issue'
        ds = self.__get_data_source(type_)
        raw_attributes = self.__convert_attributes(type_, transfer['fields'])
        return ds.data_object_factory(
            type_,
            id_=transfer.get('key'),
            attributes={
                k: v for k, v in raw_attributes.items()
                if k not in ['key'] and k in ds.attribute_types[type_]
            } | {
                'status_changes': self.__parse_issue_status_changelog(transfer)
            },
            to_one={
                k: self.__parse_user(v) for k, v in raw_attributes.items()
                if k in ds.relationship_config[type_].to_one
            }
        )

    def __parse_user(self, transfer: JiraTransfer) -> DataObject:
        if transfer is None:
            return None
        type_ = 'user'
        ds = self.__get_data_source(type_)
        raw_attributes = transfer
        return ds.data_object_factory(
            type_,
            id_=transfer.get('key'),
            attributes={k: v for k, v in raw_attributes.items()
                        if k not in ['key'] and k in ds.attribute_types[type_]}
        )

    def __parse_issue_status_changelog(self, transfer: JiraTransfer) -> DataObject:
        if transfer is None:
            return None
        status_changes = []
        previous_date = self.__parse_date(transfer['fields']['created'])
        for history in transfer['changelog']['histories']:
            for item in history['items']:
                if item['field'] == 'status':
                    end_date = self.__parse_date(history['created'])
                    status_changes.append({
                        'this_status': item['fromString'],
                        'next_status': item['toString'],
                        'start_date': previous_date,
                        'end_date': end_date
                    })
                    previous_date = end_date
        return status_changes

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__dict[type_]

    def __convert_attributes(
            self,
            type_: str,
            attributes: dict[str, Any]
    ) -> dict[str, Any]:
        ret = {}
        ds = self.__get_data_source(type_)
        for key, value in attributes.items():
            if key in self.__IGNORE_FIELDS:
                continue
            if key in self.__field_mappings:
                ret[self.__field_mappings[key]['system_name']] = \
                    self.__convert_field_value(
                        self.__field_mappings[key]['jira_type'],
                        self.__field_mappings[key]['jira_item_type'],
                        value)
            if type_ in ds.relationship_config and \
                    key in ds.relationship_config[type_].to_one:
                ret[key] = value
        return ret

    def __convert_field_value(self, type_: str, item_type: str, value: Any) -> Any:
        if value is None:
            return None
        elif type_ == 'datetime':
            return self.__parse_date(value)
        elif type_ == 'option':
            return value['value']
        elif type_ == 'array':
            return_value = []
            for array_item in value:
                return_value.append(self.__convert_field_value(item_type, 'string', array_item))
            return return_value
        elif type_ == 'progress':
            return value['progress']
        elif isinstance(value, dict) and 'name' in value:  # Internal Jira types
            return value['name']
        else:
            return value

    def __parse_date(self, date: str) -> str:
        if date is None:
            return None
        return dateutil_parse(date, ignoretz=True)
