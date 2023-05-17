# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from os import path

import requests_mock

import tol.barcodes


def mock_everything(f):
    def wrapper():
        with requests_mock.Mocker() as m:
            pmb_url = 'http://afake.address.ac.uk:9292'
            baracoda_url = 'https://anotherfake.address.ac.uk'
            m.register_uri(
                'POST',
                path.join(baracoda_url, 'barcodes_group', 'TEST', 'new?count=3'),
                status_code=201,
                json={
                    'barcodes_group': {
                        'barcodes': [
                            'TEST-111110',
                            'TEST-111111',
                            'TEST-111112',
                        ],
                        'id': 122349,
                    }
                },
            )
            m.register_uri(
                'POST',
                path.join(baracoda_url, 'barcodes_group', 'TEST', 'new?count=1'),
                status_code=201,
                json={'barcodes_group': {'barcodes': ['TEST-111110'], 'id': 122349}},
            )
            m.register_uri(
                'GET',
                path.join(pmb_url, 'v1', 'printers'),
                json={
                    'data': [
                        {
                            'id': '1',
                            'type': 'printers',
                            'attributes': {
                                'name': 'printer_a',
                                'protocol': 'LPD',
                                'printer_type': 'toshiba',
                            },
                        }
                    ]
                },
            )
            m.register_uri(
                'GET',
                path.join(pmb_url, 'v1', 'label_templates'),
                json={
                    'data': [
                        {
                            'id': '2',
                            'type': 'label_templates',
                            'attributes': {'name': 'label_template_b'},
                        }
                    ]
                },
            )
            m.register_uri(
                'GET',
                path.join(pmb_url, 'v1', 'label_templates', '2'),
                json={
                    'data': {
                        'id': '2',
                        'type': 'label_templates',
                        'attributes': {'name': 'label_template_b'},
                    },
                    'included': [
                        {
                            'id': '4',
                            'type': 'bitmaps',
                            'attributes': {'field_name': 'required_field_1'},
                        },
                        {
                            'id': '5',
                            'type': 'bitmaps',
                            'attributes': {'field_name': 'required_field_2'},
                        },
                    ],
                },
            )
            m.register_uri(
                'POST',
                path.join(pmb_url, 'v2', 'print_jobs'),
                status_code=200,
                text='SUCCESS',
            )
            f()

    return wrapper


@mock_everything
def test_printers_success():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    response = barcodes.printers()
    assert response == {
        'status_code': 200,
        'message': 'SUCCESS',
        'data': [{'id': '1', 'name': 'printer_a', 'type': 'toshiba'}],
    }


@mock_everything
def test_label_templates_success():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    response = barcodes.label_templates()
    assert response == {
        'status_code': 200,
        'message': 'SUCCESS',
        'data': [{'id': '2', 'name': 'label_template_b'}],
    }


@mock_everything
def test_required_fields_success():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    response = barcodes.required_fields('label_template_b')
    assert response == {
        'status_code': 200,
        'message': 'SUCCESS',
        'data': ['label_name', 'required_field_1', 'required_field_2'],
    }


@mock_everything
def test_print_labels_validation_error():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_x': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.print_labels(
        label_data, 'printer_a', 'label_template_b', dry=False
    )
    assert response == {
        'status_code': 400,
        'message': 'Validation error',
        'data': {
            'required_field_1': ['Missing data for required field.'],
            'required_field_x': ['Unknown field.'],
        },
    }


@mock_everything
def test_print_labels_success():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_1': 'abc123',
            'required_field_2': 'abc345',
        },
        {
            'barcode': 'COS00002',
            'required_field_1': 'abc124',
            'required_field_2': 'abc346',
        }
    ]
    response = barcodes.print_labels(
        label_data, 'printer_a', 'label_template_b', dry=False
    )
    assert response == {'status_code': 200, 'message': 'SUCCESS', 'data': {}}


@mock_everything
def test_print_labels_limit_error():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_1': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.print_labels(
        label_data, 'printer_a', 'label_template_b', copies=501, dry=False
    )
    assert response == {
        'status_code': 403,
        'message': 'Requested to print more barcodes than limit of 500',
        'data': {}
    }


@mock_everything
def test_print_labels_pass_dry():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_1': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.print_labels(
        label_data, 'printer_a', 'label_template_b', dry=True
    )
    assert response == {
        'status_code': 200,
        'message': 'Dry run',
        'data': {}
    }


@mock_everything
def test_generate_pass():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 500,
            'print_limit': 500,
        }
    )
    response = barcodes.generate('TEST', 3)
    assert response == {
        'status_code': 200,
        'message': 'SUCCESS',
        'data': ['TEST-111110', 'TEST-111111', 'TEST-111112'],
    }


@mock_everything
def test_generate_pass_with_limit():
    barcodes = tol.barcodes.Interface(
        {
            'pmb_url': 'http://afake.address.ac.uk:9292',
            'baracoda_url': 'https://anotherfake.address.ac.uk',
            'generate_limit': 1,
            'print_limit': 500,
        }
    )
    response = barcodes.generate('TEST', 3)
    assert response == {
        'status_code': 403,
        'message': 'Requested to generate more barcodes than limit of 1',
        'data': {}
    }
