# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from os import getenv, path

from marshmallow import Schema, fields

import requests


class Interface:

    def __init__(self, config):
        self.pmb_url = config['pmb_url']
        self.barcodebar_url = config['barcodebar_url']

    def printers(self):
        """Show all printers"""
        printers = []
        response = requests.get(path.join(self.pmb_url, 'v1', 'printers'))
        for i in response.json()['data']:
            printers += [
                {
                    'id': i['id'],
                    'name': i['attributes']['name'],
                    'type': i['attributes']['printer_type'],
                }
            ]
        return printers

    def label_templates(self):
        """Show all label-templates"""
        response = requests.get(path.join(self.pmb_url, 'v1', 'label_templates'))
        label_templates = []
        for i in response.json()['data']:
            label_templates += [{'id': i['id'], 'name': i['attributes']['name']}]
        return label_templates

    def required_fields(self, label_template_name):
        """Show all required fields for a label template"""
        _id = {label['name']: label['id'] for label in self.label_templates()}[
            label_template_name
        ]
        response = requests.get(path.join(self.pmb_url, 'v1', 'label_templates', _id))
        required_fields = []
        for i in response.json()['data']['included']:
            if i['type'] == 'bitmaps':
                required_fields += [i['attributes']['field_name']]
        return required_fields

    def generate_barcodes(self, prefix, number):
        """Generate barcodes with given prefix"""
        barcoda_url = getenv('BARCODA_URL')
        barcodes = []
        for i in range(0, number):
            response = requests.post(
                path.join(barcoda_url, 'barcodes', prefix, 'new'), verify=False
            )
            barcode = response.json()['barcode']
            barcodes += [barcode]
        return barcodes

    def label_schema(self, required_fields):
        """Marshmallow schema from list of required fields"""
        schema_dict = {'barcode': fields.Str(required=True)}
        for field in required_fields:
            schema_dict[field] = fields.Str(required=True)
        return Schema.from_dict(schema_dict)

    def validate_label_data(self, label_data, label_template_name):
        """Validate a label from a template name"""
        schema = self.label_schema(self.required_fields(label_template_name))
        for label in label_data:
            return schema().validate(label)

    def print_labels(
            self,
            label_data,
            printer_name,
            label_template_name,
            copies=1, dry=True
    ):
        """Print labels"""
        validation = self.validate_label_data(label_data, label_template_name)
        if validation != {}:
            return {'ValidationError': validation}
        else:
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
                response = requests.post(url, json=json.dumps(job))
                return {'Response': response.json()}
            else:
                curl = (
                    "curl -d '"
                    + json.dumps(job, indent=4)
                    + "' -H 'Content-Type: application/vnd.api+json' -X POST "
                    + url
                )
                return {'DryRun': curl}
