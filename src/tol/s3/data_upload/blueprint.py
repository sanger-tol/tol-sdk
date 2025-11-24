# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tempfile import NamedTemporaryFile
from typing import Any

from flask import Blueprint, request, send_file

from tol.api_base import (
    custom_blueprint,
)
from ...services.s3_client import S3Client


ALLOWED_EXTENSIONS: set[str] = {'csv', 'json', 'xlsx'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def data_upload_blueprint(
    url_prefix: str = '/pipeline/data_upload',
) -> Blueprint:

    data_upload_blueprint = custom_blueprint(
        name='data_upload',
        url_prefix=url_prefix
    )

    @data_upload_blueprint.route('/upload', methods=['POST'])
    def upload_file() -> tuple[dict[str, str], int]:
        file = request.files['file']
        s3_bucket: str = request.form.get('s3_bucket')

        if not file:
            return {'error': 'No file provided'}, 400

        if not allowed_file(file.filename):
            return {'error': 'File type not allowed'}, 400

        if not s3_bucket:
            return {'error': 'S3 bucket not specified'}, 400

        try:
            s3_client = S3Client()
            with NamedTemporaryFile() as temp_file:
                file.save(temp_file.name)
                s3_client.put_object(s3_bucket, file.filename, temp_file.name)

            return {'message': 'File uploaded successfully'}, 200

        except Exception as e:
            return {'error': f'Failed to upload file: {str(e)}'}, 500

    @data_upload_blueprint.route('/download', methods=['POST'])
    def download_file() -> tuple[dict[str, str], int]:
        body: dict[str, Any] = request.json.get('data', {})

        if 's3_bucket' not in body or 'file_name' not in body:
            return {'error': 'S3 bucket or file name not specified'}, 400

        bucket_name = body['s3_bucket']
        file_name = body['file_name']

        try:
            s3_client = S3Client()

            with NamedTemporaryFile() as temp_file:
                s3_client.get_object(bucket_name, file_name, temp_file.name)
                download_name = request.json.get('download_name', file_name)

                return send_file(
                    temp_file.name,
                    as_attachment=True,
                    download_name=download_name,
                    mimetype='application/octet-stream'
                )
        except Exception as e:
            return {'error': f'Failed to download file: {str(e)}'}, 500

    return data_upload_blueprint
