# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# curl -D- -X POST -H "Authorization: Bearer MDM4MTc2MDc3MDUxOgkkaGWwUAMdfaiLiIeS6idd0K9j" -H "Content-Type: application/json" --data '{"jql":"status = curation and project in (RC,GRIT)","maxResults":1}' https://jira.sanger.ac.uk/rest/api/latest/search

import requests
import pandas as pd
import json
# import hashlib
# import json
# from collections.abc import Callable
# from datetime import datetime
from functools import cache
from typing import Any, Dict, Iterable, Tuple

# from caseconverter import (
#     kebabcase,
#     snakecase
# )

# from elasticsearch import (Elasticsearch, helpers)

from ..api_base.utils import parse_filters

from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import PageGetter


class TreevalDataSource(
    DataSource,
    PageGetter,
):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['url', 'api_token'])
        # self._initialise_elasticsearch()

    # def _initialise_elasticsearch(self):
    #     self.es = Elasticsearch(self.uri, http_auth=(self.user, self.password))
    #     self.helpers = helpers
# ,"fields":["key","fields"]
    def _build_jira_query(self):
        return '{"jql":"status = curation and project in (RC,GRIT)","maxResults":1000,"expand":["changelog"]}'

    def _execute_jira_query(self, query):
        response = requests.post(
            url = f"https://{self.url}/rest/api/latest/search",
            headers={'Authorization': 'Bearer ' + self.api_token, 'Content-Type': 'application/json'},
            data = query
        )

        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to JIRA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response.json()

    def _parse_jira_output(self, response_text):

        issues = map(self._get_values_from_issue, response_text['issues'])

        return pd.DataFrame(issues)

    def _get_values_from_issue(self,issue):
        key = issue['key']
        fields = issue['fields']
        updated = str(fields['updated'])
        treeval_val = fields['customfield_12200']
        species_name = self._parse_species_name(fields['customfield_11676'])
        tolid = self._parse_species_id(fields['summary'])
        assignee = fields['assignee']

        if assignee:
            display_name = assignee['displayName']
        else:
            display_name = "Unassigned"

        jbrowse_status_value = None
        jbrowse_link = None
        if treeval_val:
            if treeval_val.startswith("http"):
                jbrowse_link = treeval_val
                jbrowse_status_value = "jBrowse"

        return {'tolid': tolid,
                'species_name': species_name,
                'jira_issue': key, 
                'jira_issue_link': f'https://{self.url}/browse/{key}', 
                'jira_issue_last_updated': updated, 
                'jbrowse_link': jbrowse_link, 
                'assignee': display_name, 
                'jbrowse_status': jbrowse_status_value 
                }

    def _parse_species_name(self,species_name):
        if species_name:

            # Trim unused common name
            suffix = ' ()'
            if species_name.endswith(suffix):
                species_name = species_name[:-len(suffix)]

            return species_name
        else:
            return ''

    def _parse_species_id(self,summary):
        species_id = str(summary)

        if species_id != '':
            species_id = species_id.replace(' GenomeArk assembly', '')
            species_id = species_id.replace(' ERGA assembly', '')
            species_id = species_id.replace(' Darwin assembly', '')
            species_id = species_id.replace(' faculty assembly', '')
            species_id = species_id.replace(' ASG assembly', '')
            species_id = species_id.replace(' VGP assembly', '')
            species_id = species_id.replace(' external assembly', '')
            species_id = species_id.replace(' assembly', '')

            return species_id
        else:
            return ''


    def _apply_filter_to_specimens(self,object_filters,specimens):

        if 'tolid' in object_filters:
            # raise DataSourceError(title=specimens['tolid'])
            specimens = specimens[specimens['tolid'].str.contains(object_filters['tolid'])]

        if 'species_name' in object_filters:
            specimens = specimens[specimens['species_name'].str.contains(object_filters['species_name'])]

        if 'jira_issue' in object_filters:
            specimens = specimens[specimens['jira_issue'].str.contains(object_filters['jira_issue'])]

        if 'jira_issue_link' in object_filters:
            specimens = specimens[specimens['jira_issue_link'].str.contains(object_filters['jira_issue_link'])]

        if 'jira_issue_last_updated' in object_filters:
            specimens = specimens[specimens['jira_issue_last_updated'].str.contains(object_filters['jira_issue_last_updated'])]

        if 'jbrowse_link' in object_filters:
            specimens = specimens[specimens['jbrowse_link'].str.contains(object_filters['jbrowse_link'])]

        if 'assignee' in object_filters:
            specimens = specimens[specimens['assignee'].str.contains(object_filters['assignee'])]

        if 'jbrowse_status' in object_filters:
            specimens = specimens[specimens['jbrowse_status'].str.contains(object_filters['jbrowse_status'])]

        # for key, val in object_filters.contains.items():
        #     specimens.loc[specimens[key] == val]

        return specimens


    def _apply_sort_to_specimens(self,sort_by,specimens):

        if sort_by is None:
            column_name = 'jira_issue_last_updated'
            sort_direction = False
        else:
            if sort_by.startswith('-'):
                column_name = sort_by[1:]
                sort_direction = False
            else:
                column_name = sort_by
                sort_direction = True
        
        specimens = specimens.sort_values(by=[column_name], ascending=sort_direction)

        return specimens

    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        page_size: int = None,
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:

        query = self._build_jira_query()
        response = self._execute_jira_query(query)

        # Convert raw jira output data to visible outputs.
        specimens = self._parse_jira_output(response)

        #object_filters needs to be dict - currently string
        object_filters_dict = json.loads(object_filters)
        # Filter
        if object_filters_dict and len(object_filters_dict.keys()) > 0:
            # raise DataSourceError(title=object_filters_dict)
            contains_filter = object_filters_dict["exact"]
            specimens = self._apply_filter_to_specimens(contains_filter, specimens)

        # Sort
        specimens = self._apply_sort_to_specimens(sort_by, specimens)

        full_len = len(specimens)

        if not page_size:
            page_size = 50

        if not page:
            page = 1

        end_val = int(page) * int(page_size)
        start_val = end_val - int(page_size)

        if len(specimens) < end_val:        
            end_val = len(specimens)

        # Filter to current page
        specimens = specimens.iloc[start_val:end_val,]
        
        return (specimens.to_dict("records"), full_len)

        # index = self.__get_index(object_type)
        # query = self._build_elasticsearch_query(object_type, object_filters)
        # sort = self._build_elasticsearch_sort(object_type, sort_by)
        # if page_size is None:
        #     page_size = self.get_page_size()
        # from_ = (page - 1) * page_size
        # resp = self.es.search(
        #     from_=from_,
        #     size=page_size,
        #     index=index,
        #     query=query,
        #     sort=sort
        # )
        # return self._convert_dict_to_data_objects(resp['hits']['hits']), \
        #     resp['hits']['total']['value']

    def get_specimens_for_treeval(self, page_number, page_size, filter_, sort_by):

        specimens_page, total_specimen_count = self.get_list_page(object_type="specimen", page=page_number, object_filters=filter_, sort_by=sort_by, page_size=page_size)

        return {'total': total_specimen_count, 'data': specimens_page} 

    def get_specimen_for_treeval(self, tolid):
        return self.get_specimens_for_treeval(1, 1, f'[tolid={tolid}]', 'tolid')[0]

    # def _convert_data_object_to_dict(self, data_object: DataObject) -> Dict:
    #     return data_object.attributes

    # def _prefix_fields(self, dict_: Dict, prefix: str) -> Dict:
    #     if prefix == '':
    #         return dict_
    #     ret = {}
    #     for k, v in dict_.items():
    #         ret[prefix + '_' + k] = v
    #     return ret

    # def _add_updated(self, dict_: Dict) -> Dict:
    #     return {**dict_, 'tol_updated_at': datetime.now().isoformat()}

    # def _add_checksum(self, dict_: Dict) -> Dict:
    #     dhash = hashlib.sha256()
    #     encoded = json.dumps(dict_, sort_keys=True, default=str).encode()
    #     dhash.update(encoded)
    #     return {**dict_, 'checksum': dhash.hexdigest()}

    # def _add_uid(self, dict_: Dict, uid: Any) -> Dict:
    #     return {**dict_, 'uid': f'{uid}'}

    # def _convert_dates(self, dict_: Dict) -> Dict:
    #     ret = {}
    #     for k, v in dict_.items():
    #         if isinstance(v, datetime):
    #             ret[k] = v.isoformat()
    #         else:
    #             ret[k] = v
    #     return ret

    # def __get_index(self, object_type: str) -> str:
    #     return f'{self.index_prefix}-{kebabcase(object_type)}'

    # def __get_object_type(self, index: str) -> str:
    #     start = len(self.index_prefix) + 1
    #     return snakecase(index[start:])

    # def _field_or_keyword(self, object_type: str, name: str):
    #     field_type = self.get_attribute_types(object_type)[name]
    #     if field_type == 'str':
    #         return f'{name}.keyword'
    #     return name

    # def get_by_id(
    #     self,
    #     object_type: str,
    #     object_ids: Iterable[DataId],
    #     **kwargs
    # ) -> Iterable[DataObject]:
    #     index = self.__get_index(object_type)
    #     resp = self.es.mget(
    #         body={'ids': object_ids},
    #         index=index
    #     )
    #     return self._convert_dict_to_data_objects(resp['docs'])







    # def _build_elasticsearch_query(self, object_type: str,
    #                                object_filters: DataSourceFilter = None):
    #     if object_filters is None:
    #         return
    #     query = {'bool': {'must': [], 'must_not': []}}
    #     if object_filters.exact is not None:
    #         for k, v in object_filters.exact.items():
    #             if v is None:
    #                 query['bool']['must_not'].append({'exists': {'field': k}})
    #             else:
    #                 search_field = self._field_or_keyword(object_type, k)
    #                 query['bool']['must'].append({'match': {search_field: v}})

    #     if object_filters.contains is not None:
    #         for k, v in object_filters.contains.items():
    #             search_field = self._field_or_keyword(object_type, k)
    #             query['bool']['must'].append({'wildcard': {search_field:
    #                                                        {'value': f'{v}*', 'boost': 1.0}}})
    #     if object_filters.in_list is not None:
    #         for k, v in object_filters.in_list.items():
    #             query['bool']['must'].append({'terms': {k: v, 'boost': 1.0}})

    #     if object_filters.range is not None:
    #         for k, v in object_filters.range.items():
    #             query['bool']['must'].append({'range': {k: {'gte': v['from'],
    #                                                         'lte': v['to']}}})

    #     return query

    # def _build_elasticsearch_sort(self, object_type: str, sort_by: str):
    #     default_sort = {'uid.keyword': 'asc'}
    #     if sort_by is None:
    #         return [default_sort]
    #     if sort_by.startswith('-'):
    #         field = self._field_or_keyword(object_type, sort_by[1:])
    #         order = 'desc'
    #     else:
    #         field = self._field_or_keyword(object_type, sort_by)
    #         order = 'asc'
    #     sort = [{field: order}, default_sort]
    #     return sort

    # def get_list(
    #     self,
    #     object_type: str,
    #     object_filters: DataSourceFilter = None,
    #     **kwargs
    # ) -> Iterable[DataObject]:
    #     index = self.__get_index(object_type)
    #     query = self._build_elasticsearch_query(object_type, object_filters)
    #     generator = self.helpers.scan(self.es,
    #                                   index=index,
    #                                   scroll='10m',
    #                                   size=500,
    #                                   query={'query': query})
    #     return self._convert_dict_to_data_objects(generator)

    # def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable:
    #     for obj in objs:
    #         yield self.data_object_factory(
    #             self.__get_object_type(obj['_index']),
    #             data={
    #                 **obj['_source'],
    #                 'id': obj['_id']
    #             }
    #         )

    # def get_aggregations(
    #         self,
    #         object_type: str,
    #         aggregations: Dict,
    #         object_filters: DataSourceFilter = None,
    # ) -> Dict:
    #     index = self.__get_index(object_type)
    #     query = self._build_elasticsearch_query(object_type, object_filters)
    #     resp = self.es.search(
    #         size=0,
    #         index=index,
    #         query=query,
    #         aggregations=aggregations
    #     )
    #     return resp['aggregations']

    @property
    @cache
    def supported_types(self):
        index_names = self.es.cat.indices(h='index', s='index').split()
        return [self.__get_object_type(index_name)
                for index_name in index_names
                if index_name.startswith(self.index_prefix)]

    # def __map_type(self, type_: str) -> str:
    #     if type_ == 'text':
    #         return 'str'
    #     if type_ == 'long':
    #         return 'int'
    #     if type_ == 'date':
    #         return 'datetime'
    #     return type_

    @cache
    def get_attribute_types(self, object_type: str) -> Dict:
        index_name = self.__get_index(object_type)
        mapping = self.es.indices.get_mapping(index_name)
        if 'properties' not in mapping[index_name]['mappings']:
            return {}
        properties = mapping[index_name]['mappings']['properties']
        return {
            property_name: self.__map_type(properties[property_name]['type'])
            for property_name in properties
            if 'type' in properties[property_name]
        }
