# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import xml.etree.ElementTree as ElementTree
from functools import cache
from typing import Callable, Dict, Iterable, Optional, Tuple

from cachetools.func import ttl_cache

import requests
from requests.auth import HTTPBasicAuth


from .client import EnaApiClient
from .converter import (
    EnaApiConverter
)
from .ena_methods import (
    assign_ena_ids,
    build_bundle_sample_xml,
    build_submission_xml,
    convert_checklist_xml_to_dict,
    convert_xml_to_list_of_sample_dict,
)
from .filter import (
    EnaFilter
)
from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import (
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
)
from ..core.relationship import RelationshipConfig

ClientFactory = Callable[[], EnaApiClient]
FilterFactory = Callable[[], EnaFilter]
EnaConverterFactory = Callable[[], EnaApiConverter]


class EnaDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational
):
    """
    A `Datasource` that connects to a remote ENA API.

    Developers should likely use `create_ena_data_source`
    instead of this directly
    """
    def __init__(
        self,
        client_factory: ClientFactory,
        ena_converter_factory: EnaConverterFactory,
        filter_factory: FilterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__ec_factory = ena_converter_factory
        self.__filter_factory = filter_factory
        super().__init__({})

    @ttl_cache(ttl=60)
    def get_fields(self, object_type) -> dict:
        return self.__client_factory().get_fields(object_type)

    def __get_filter_string(
        self,
        object_filters=Optional[DataSourceFilter]
    ) -> Optional[str]:
        if object_filters is None:
            return ''

        return self.__filter_factory().dumps(object_filters)

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        att_types = {}

        for object_type in self.supported_types:
            fields = self.get_fields(object_type)
            att_types[object_type] = fields

        return att_types

    @property
    @cache
    def supported_types(self) -> list[str]:
        return ['assembly', 'read_run', 'sample', 'study', 'taxon']

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[DataObject]]:
        self.__validate_object_type(object_type)

        client = self.__client_factory()
        ena_response = client.get_detail(object_type, object_ids)
        ena_converter = self.__ec_factory()

        converted_objects, _ = ena_converter.convert_list(object_type, ena_response) \
            if ena_response is not None else ([], 0)
        yield from self.sort_by_id(converted_objects, object_ids)

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> tuple[Iterable[DataObject], int]:

        size = page_size if page_size else self.get_page_size()
        filter_string = self.__get_filter_string(object_filters)

        self.__validate_object_type(object_type)
        client = self.__client_factory()
        ena_response = client.get_list(
            object_type,
            filter_string=filter_string
        )

        converted_objects, total = self.__ec_factory().convert_list(object_type, ena_response)
        # sort by id by default
        sorted_response = sorted(converted_objects, key=lambda x: x.id)
        list_slice_objects = sorted_response[((page_number - 1) * size):(page_number * size)]

        return list_slice_objects, total

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> Iterable[DataObject]:

        if sort_by is not None:
            self.__raise_sort_by_error()

        self.__validate_object_type(object_type)
        filter_string = self.__get_filter_string(object_filters)
        client = self.__client_factory()

        ena_response = client.get_list(
            object_type,
            filter_string=filter_string
        )

        converted_objects, total = self.__ec_factory().convert_list(object_type, ena_response) \
            if ena_response is not None else ([], 0)
        yield from converted_objects

    @property
    @cache
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return {
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relation_name: str,
    ) -> Optional[DataObject]:
        return None

    def get_to_many_relations(
        self,
        source: DataObject,
        relation_name: str,
    ) -> Iterable[DataObject]:
        return []

    def post_request(self, command: str, files) -> requests.Response:
        response = requests.post(self.uri + command,
                                 files=files,
                                 auth=HTTPBasicAuth(self.user, self.password))
        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to ENA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response

    def get_request(self, command: str, headers=None, params=None) -> requests.Response:

        response = requests.get(self.uri + command,
                                params=params, headers=headers,
                                auth=HTTPBasicAuth(self.user, self.password))

        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to ENA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response

    def get_xml_checklist(self, checklist_id: str) -> Dict[str, Tuple[str, str, object]]:
        output = self.get_request(f'/ena/browser/api/xml/{checklist_id}')

        checklist_dict = convert_checklist_xml_to_dict(output.text)

        return checklist_dict

    def get_biosample_data_biosampleid(self, biosample_id: str):
        output = self.get_request(f'/ena/browser/api/xml/{biosample_id}')

        samples = convert_xml_to_list_of_sample_dict(output.text)

        # Only returning one sample for biosample
        return samples[0]

    def generate_ena_ids_for_samples(self, manifest_id: str,
                                     samples: Dict[str, Dict]) -> Tuple[str, Dict[str, Dict]]:

        bundle_xml_file, sample_count = build_bundle_sample_xml(samples)

        with open(bundle_xml_file, 'r') as bxf:
            bundle_xml_file_contents = bxf.read()

            element = ElementTree.XML(bundle_xml_file_contents)
            ElementTree.indent(element)
            bundle_xml_file_contents = ElementTree.tostring(element, encoding='unicode')

        if sample_count == 0:
            raise DataSourceError(title='All samples have unknown taxonomy ID',
                                  detail='')

        submission_xml_file = build_submission_xml(manifest_id, self.contact_name,
                                                   self.contact_email)

        xml_files = [('SAMPLE', open(bundle_xml_file, 'rb')),
                     ('SUBMISSION', open(submission_xml_file, 'rb'))]

        response = self.post_request('/ena/submit/drop-box/submit/', xml_files)

        try:
            assigned_samples = assign_ena_ids(samples, response.text)

        except Exception as ex:
            raise DataSourceError(title='Error returned from ENA service',
                                  detail=ex)

        if not assigned_samples:
            errors = {}
            error_count = 0
            for error_node in ElementTree.fromstring(response.text).findall('./MESSAGES/ERROR'):
                if error_node is not None:
                    error_count += 1
                    errors[str(error_count)] = error_node.text

            return False, errors
        else:
            return True, assigned_samples

    def __validate_object_type(self, object_type: str):
        if object_type not in self.supported_types:
            raise DataSourceError(
                title='Unsupported object type',
                detail=f"Object type '{object_type}' is not supported by this data source."
            )
