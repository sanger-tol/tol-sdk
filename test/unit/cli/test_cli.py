# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner


cli_module = importlib.import_module('tol.cli.cli')


@pytest.fixture
def sources(monkeypatch, tmp_path):
    env_file = tmp_path / 'custom.env'
    env_file.write_text('QUASAR_URL=https://example.invalid\n')
    monkeypatch.delenv('QUASAR_URL', raising=False)
    quasar_ds = Mock()
    quasar_ds.get_list.return_value = iter([
        SimpleNamespace(id='portal'),
        SimpleNamespace(id='dynamic_source'),
    ])

    def get_quasar():
        assert os.environ['QUASAR_URL'] == 'https://example.invalid'
        return quasar_ds

    quasar_mock = Mock(side_effect=get_quasar)
    monkeypatch.setattr(cli_module, 'quasar', quasar_mock)
    return env_file, quasar_mock, quasar_ds


def test_source_choice_uses_quasar_and_env_file(sources, monkeypatch):
    env_file, quasar_mock, quasar_ds = sources
    data_source = Mock()
    data_source.get_list.return_value = []
    get_datasource = Mock(return_value=data_source)
    monkeypatch.setattr(cli_module.DataSourceUtils, 'get_datasource', get_datasource)

    result = CliRunner().invoke(
        cli_module.cli,
        ['--env-file', str(env_file), 'data', '--source', 'dynamic_source', '--type', 'sample'],
    )

    assert result.exit_code == 0, result.output
    quasar_mock.assert_called_once_with()
    quasar_ds.get_list.assert_called_once_with('data_source_instance')
    get_datasource.assert_called_once_with('dynamic_source')
    data_source.get_list.assert_called_once()


def test_source_choice_rejects_unknown_source(sources):
    env_file, quasar_mock, _ = sources
    result = CliRunner().invoke(
        cli_module.cli,
        ['--env-file', str(env_file), 'data', '--source', 'unknown', '--type', 'sample'],
    )

    assert result.exit_code == 2
    assert "'unknown' is not one of 'portal', 'dynamic_source'" in result.output
    quasar_mock.assert_called_once_with()


def test_data_help_lists_dynamic_sources(sources):
    env_file, quasar_mock, _ = sources
    result = CliRunner().invoke(cli_module.cli, ['--env-file', str(env_file), 'data', '--help'])

    assert result.exit_code == 0, result.output
    assert '[portal|dynamic_source]' in result.output
    quasar_mock.assert_called_once_with()


def test_source_choices_refresh_for_each_invocation(sources):
    env_file, quasar_mock, quasar_ds = sources
    quasar_ds.get_list.side_effect = [
        iter([SimpleNamespace(id='first')]),
        iter([SimpleNamespace(id='second')]),
    ]
    runner = CliRunner()

    first = runner.invoke(cli_module.cli, ['--env-file', str(env_file), 'data', '--help'])
    second = runner.invoke(cli_module.cli, ['--env-file', str(env_file), 'data', '--help'])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert '[first]' in first.output
    assert '[second]' in second.output
    assert quasar_mock.call_count == 2


def test_root_help_does_not_fetch_sources(sources):
    _, quasar_mock, _ = sources
    result = CliRunner().invoke(cli_module.cli, ['--help'])

    assert result.exit_code == 0, result.output
    quasar_mock.assert_not_called()


def test_source_shell_completion(sources):
    env_file, quasar_mock, _ = sources
    result = CliRunner().invoke(
        cli_module.cli,
        prog_name='tol',
        env={
            '_TOL_COMPLETE': 'bash_complete',
            'COMP_WORDS': f'tol --env-file {env_file} data --source dyn',
            'COMP_CWORD': '5',
        },
    )

    assert result.exit_code == 0, result.output
    assert 'dynamic_source' in result.output
    quasar_mock.assert_called_once_with()


def test_quasar_failure_is_not_silenced(monkeypatch):
    def fail():
        raise RuntimeError('Quasar unavailable')

    monkeypatch.setattr(cli_module, 'quasar', fail)
    result = CliRunner().invoke(cli_module.cli, ['data', '--help'])

    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == 'Quasar unavailable'
