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
                        'included': [
                            {
                                'id': '4',
                                'type': 'bitmaps',
                                'attributes': {
                                    'field_name': 'required_field_1'
                                },
                            },
                            {
                                'id': '5',
                                'type': 'bitmaps',
                                'attributes': {
                                    'field_name': 'required_field_2'
                                },
                            },
                        ],
                    }
                },
            )
            m.register_uri(
                'POST',
                path.join(pmb_url, 'v2', 'print_jobs'),
                status_code=200,
                json='message',
            )
            f()

    return wrapper


@mock_everything
def test_printers():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    response = barcodes.printers()
    assert response == [{'id': '1', 'name': 'printer_a', 'type': 'toshiba'}]


@mock_everything
def test_label_templates():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    response = barcodes.label_templates()
    assert response == [{'id': '2', 'name': 'label_template_b'}]


@mock_everything
def test_required_fields():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    response = barcodes.required_fields('label_template_b')
    assert response == [
        'required_field_1',
        'required_field_2',
    ]


@mock_everything
def test_validate_pass():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_1': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.validate_label_data(label_data, 'label_template_b')
    assert response == {}


@mock_everything
def test_validate_fail():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_x': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.validate_label_data(label_data, 'label_template_b')
    print(response)
    assert response == {
        'required_field_1': ['Missing data for required field.'],
        'required_field_x': ['Unknown field.'],
    }


@mock_everything
def test_print_labels_fail():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
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
    assert 'ValidationError' in response.keys()


@mock_everything
def test_print_labels_pass():
    barcodes = tol.barcodes.Interface({
        'pmb_url': 'http://afake.address.ac.uk:9292',
        'barcodebar_url': 'https://anotherfake.address.ac.uk'
    })
    label_data = [
        {
            'barcode': 'COS00001',
            'required_field_1': 'abc123',
            'required_field_2': 'abc345',
        }
    ]
    response = barcodes.print_labels(
        label_data, 'printer_a', 'label_template_b', dry=False
    )
    assert response == {'Response': 'message'}
