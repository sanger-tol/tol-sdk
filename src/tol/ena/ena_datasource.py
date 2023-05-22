# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import xml.etree.ElementTree as ElementTree
from typing import Dict, Iterable, Tuple
import json

import requests
from requests.auth import HTTPBasicAuth

import tol.ena.ena_methods as em

from ..core import (
    CoreDataObject,
    DataSourceError,
    DataSourceFilter,
    DataSource,
    unsupported    
)

class EnaDataSource(DataSource):

    def __init__(self, config: Dict):

        super().__init__(config,
                         expected=['uri', 'user', 'password', 'contact_name', 'contact_email'])

    def post_request(self, command: str, files) -> requests.Response:
        response = requests.post(self.uri + command,
                                 files=files,
                                 auth=HTTPBasicAuth(self.user, self.password))
        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to ENA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response

    def get_request(self, command: str) -> requests.Response:
        response = requests.get(self.uri + command,
                                auth=HTTPBasicAuth(self.user, self.password))

        if (response.status_code != 200):
            raise DataSourceError(title='Cannot connect to ENA',
                                  detail=f"(status code '{str(response.status_code)}')'")

        return response

    def _get_field_mappings_ena(self):
        return {
            "project_name":"project_name"
        }

    def _get_ena_xml_search_query(self):
        return {
            "project_name":"project_name"
        }
        sql = f"""
        
        
        """

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[CoreDataObject]:

        if object_type != 'sample':
            raise DataSourceError('Only objects of type sample are supported')
        if object_filters is None or \
                not isinstance(object_filters.contains, dict) or \
                'project_name' not in object_filters.contains:
            raise DataSourceError('Filter must contain project_name contains filter')

        #  output = self.get_request(f'/ena/browser/api/xml/{checklist_id}')
        output = self.get_request(f'/ena/browser/api/xml/search?result=sample&query=project_name%3D%22DTOL%22&limit=10&fields=all&includeLinks=false')

        # request_data_dict = json.loads(output.text)
        return output.text
        # return CoreDataObject(object_type, data=request_data_dict)


    def get_xml_checklist(self, checklist_id: str) -> Dict[str, Tuple[str, str, object]]:
        output = self.get_request(f'/ena/browser/api/xml/{checklist_id}')

        checklist_dict = em.convert_checklist_xml_to_dict(output.text)

        return checklist_dict

    def get_biosample_data_biosampleid(self, biosample_id: str):
        output = self.get_request(f'/ena/browser/api/xml/{biosample_id}')

        samples = em.convert_xml_to_list_of_sample_dict(output.text)

        # Only returning one sample for biosample
        return samples[0]

    def generate_ena_ids_for_samples(self, manifest_id: str,
                                     samples: Dict[str, Dict]) -> Tuple[str, Dict[str, Dict]]:

        bundle_xml_file, sample_count = em.build_bundle_sample_xml(samples)

        with open(bundle_xml_file, 'r') as bxf:
            bundle_xml_file_contents = bxf.read()

            element = ElementTree.XML(bundle_xml_file_contents)
            ElementTree.indent(element)
            bundle_xml_file_contents = ElementTree.tostring(element, encoding='unicode')

        if sample_count == 0:
            raise DataSourceError(title='All samples have unknown taxonomy ID',
                                  detail='')

        submission_xml_file = em.build_submission_xml(manifest_id, self.contact_name,
                                                      self.contact_email)

        xml_files = [('SAMPLE', open(bundle_xml_file, 'rb')),
                     ('SUBMISSION', open(submission_xml_file, 'rb'))]

        response = self.post_request('/ena/submit/drop-box/submit/', xml_files)

        try:
            assigned_samples = em.assign_ena_ids(samples, response.text)

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


    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass

    @property
    def supported_types(self):
        raise NotImplementedError()

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()
