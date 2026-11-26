# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from click.testing import CliRunner

from tol.cli import cli


def query_record(*options):
    result = CliRunner().invoke(
        cli,
        [
            'data',
            '--source', 'test',
            '--type', 'record',
            '--filter', json.dumps({'and_': {'id': {'eq': {'value': '1'}}}}),
            *options,
        ],
    )
    assert result.exit_code == 0, f'{result.output}\n{result.exception!r}'
    return result.output


def test_data_ndjson():
    records = [json.loads(line) for line in query_record().splitlines()]

    assert len(records) == 1
    assert records[0]['id'] == '1'
    assert records[0]['little_string'] == 'b'
    assert records[0]['bool'] is False
    assert records[0]['int'] == 1


def test_data_tsv():
    output = query_record('--output', 'tsv', '--fields', 'little_string,bool,int')

    assert output.splitlines() == ['little_string\tbool\tint', 'b\tFalse\t1']
