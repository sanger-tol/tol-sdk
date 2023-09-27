# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from os import path

from marshmallow import Schema, fields

import requests

from ..core import DataSource


class Interface(DataSource):
    def __init__(self, config):
        # pmb_url baracoda_url, generate_limit, print_limit
        super().__init__(config)

    def custom_response(self, status_code=200, message='SUCCESS', data={}):
        return {'status_code': status_code, 'message': message, 'data': data}

    def printers(self):
        """Show all printers"""
        printers = []
        try:
            response = requests.get(path.join(self.pmb_url, 'v1', 'printers'))
        except requests.exceptions.RequestException as error:
            return self.custom_response(status_code=421, message=str(error))
        for i in response.json()['data']:
            printers += [
                {
                    'id': i['id'],
                    'name': i['attributes']['name'],
                    'type': i['attributes']['printer_type'],
                }
            ]
        return self.custom_response(data=printers)

    def label_templates(self):
        """Show all label-templates"""
        try:
            response = requests.get(path.join(self.pmb_url, 'v1', 'label_templates'))
        except requests.exceptions.RequestException as error:
            return self.custom_response(status_code=421, message=str(error))
        if response.status_code != 200:
            raise self.custom_response(
                status_code=response.status_code, data=response.json()
            )
        label_templates = []
        for i in response.json()['data']:
            label_templates += [{'id': i['id'], 'name': i['attributes']['name']}]
        return self.custom_response(data=label_templates)

    def required_fields(self, label_template_name):
        """Show all required fields for a label template"""
        label_templates = {
            label['name']: label['id'] for label in self.label_templates()['data']
        }
        _id = label_templates[label_template_name]
        try:
            response = requests.get(
                path.join(self.pmb_url, 'v1', 'label_templates', _id)
            )
        except requests.exceptions.RequestException as error:
            return self.custom_response(status_code=421, message=str(error))
        required_fields = ['label_name']
        for i in response.json()['included']:
            if i['type'] == 'bitmaps':
                required_fields += [i['attributes']['field_name']]
        return self.custom_response(data=required_fields)

    def generate(self, prefix, number):
        """Generate barcodes with given prefix"""
        if number > self.generate_limit:
            return self.custom_response(
                403,
                message=f'Requested to generate more barcodes than limit of {self.generate_limit}'
            )
        request = path.join(
            self.baracoda_url, 'barcodes_group', str(prefix), f'new?count={number}'
        )
        try:
            response = requests.post(request)
        except requests.exceptions.RequestException as error:
            return self.custom_response(status_code=421, message=str(error))
        if response.status_code != 201:
            return self.custom_response(
                status_code=response.status_code,
                message='Baracoda error',
                data=response,
            )
        try:
            barcodes = response.json()['barcodes_group']['barcodes']
            return self.custom_response(data=barcodes)
        except requests.exceptions.RequestException as error:
            return self.custom_response(status_code=421, message=str(error))

    def _label_schema(self, label_template_name):
        """Marshmallow schema from list of required fields"""
        required_fields_response = self.required_fields(label_template_name)
        required_fields = required_fields_response['data']
        schema_dict = {'barcode': fields.Str(required=True)}
        for field in required_fields:
            schema_dict[field] = fields.Str(required=True)
        schema_dict.pop('label_name')
        return Schema.from_dict(schema_dict)

    def print_labels(
        self, label_data, printer_name, label_template_name, copies=1, dry=True
    ):
        """Print labels"""
        if copies > self.print_limit:
            return self.custom_response(
                403,
                message=f'Requested to print more barcodes than limit of {self.print_limit}'
            )

        copies = min(copies, self.print_limit)
        schema = self._label_schema(label_template_name)

        for label in label_data:
            validation = schema().validate(label)
            if validation != {}:
                return self.custom_response(
                    status_code=400, message='Validation error', data=validation
                )

        for label in label_data:
            label['label_name'] = 'main_label'

        job = {
            'print_job': {
                'printer_name': printer_name,
                'label_template_name': label_template_name,
                'labels': label_data,
                'copies': copies,
            }
        }

        url = path.join(self.pmb_url, 'v2', 'print_jobs')

        if not dry:
            try:
                response = requests.post(
                    url,
                    data=json.dumps(job),
                    headers={
                        'Content-Type': 'application/vnd.api+json',
                        'accept': 'application/json',
                    },
                )
                return self.custom_response(
                    status_code=response.status_code,
                    message=response.text
                )
            except requests.exceptions.RequestException as error:
                return self.custom_response(status_code=421, message=str(error))

        return self.custom_response(message='Dry run')

    @property
    def supported_types(self):
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()
