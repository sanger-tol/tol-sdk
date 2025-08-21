# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from tol.services.s3_client import S3Client


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv('S3_URI', 'somehost:9000')
    monkeypatch.setenv('S3_ACCESS_KEY', 'access_key')
    monkeypatch.setenv('S3_SECRET_KEY', 'secret_key')
    monkeypatch.setenv('S3_SECURE', 'false')


@patch('tol.services.s3_client.Minio')
def test_s3_client_initialization(mock_minio):
    client = S3Client()

    mock_minio.assert_called_once_with(
        'somehost:9000',
        access_key='access_key',
        secret_key='secret_key',
        secure=False
    )
    assert client.s3_uri == 'somehost:9000'


@patch('tol.services.s3_client.Minio')
def test_get_object_calls_fget_object(mock_minio):
    mock_instance = MagicMock()
    mock_minio.return_value = mock_instance
    client = S3Client()
    client.get_object('bucket', 'obj', '/tmp/file')
    mock_instance.fget_object.assert_called_once_with('bucket', 'obj', '/tmp/file')


@patch('tol.services.s3_client.Minio')
def test_list_objects_calls_list_objects(mock_minio):
    mock_instance = MagicMock()
    mock_minio.return_value = mock_instance
    client = S3Client()
    client.list_objects('bucket')
    mock_instance.list_objects.assert_called_once_with('bucket')


@patch('tol.services.s3_client.Minio')
def test_put_object_calls_fput_object(mock_minio):
    mock_instance = MagicMock()
    mock_minio.return_value = mock_instance
    client = S3Client()
    client.put_object('bucket', 'obj', '/tmp/file')
    mock_instance.fput_object.assert_called_once_with('bucket', 'obj', '/tmp/file')
