# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import importlib
import json
import os
import re
import subprocess
from uuid import uuid4

import click

from dotenv import load_dotenv

from ..core import (
    DataSourceFilter
)


@click.group()
@click.option(
    '--env-file', default='.env.dev',
    type=click.Path(), help='set a custom .env file'
)
def cli(env_file):
    pass


# Lint
@cli.command()
@click.option('--type', 'type_', default='python',
              type=click.Choice(['python', 'license', 'ui', 'ui-fix']),
              help='type of lint')
def lint(type_):
    # service = get_app()
    click.echo('Running lint...')
    if type_ == 'license':
        command = 'docker run --rm --volume $(pwd):/data fsfe/reuse:1.1.2 lint'
        click.secho(command, fg='green')
        run(command)
    if type_ == 'python':
        linter = 'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/lint:1.0.3'
        command = f'docker run --rm --volume $(pwd):/project {linter}'
        click.secho(command, fg='green')
        run(command)
    if type_ == 'ui':
        ui_linter = 'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/ui-lint:1.0.9'
        command = f'docker run --rm --volume $(pwd):/src {ui_linter}'
        click.secho(command, fg='green')
        run(command)
    if type_ == 'ui-fix':
        ui_linter = 'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/ui-lint:1.0.9 '
        command_1 = f'docker run --rm --volume $(pwd):/src {ui_linter}'
        command_2 = 'npx eslint \
            -c /project/.eslintrc \
            --ext .js,.jsx,.ts,.tsx \
            --fix \
            --ignore-pattern "**/public" \
            --ignore-pattern "**/*.license" \
            --ignore-pattern "**/Dockerfile" \
            --ignore-pattern "**/*.dev" \
            --ignore-pattern "**/*.scss" \
            /src/*-ui/**/*'
        click.secho((command_1 + command_2), fg='green')
        run(command_1 + command_2)


# Scan
@cli.command()
@click.option('--type', 'type_', default='sast',
              type=click.Choice(['sast', 'dependencies']),
              help='type of scan')
def scan(type_):
    token = os.getenv('SNYK_TOKEN')
    if token is None:
        click.secho('SNYK_TOKEN environment variable must be set', fg='red')
        return
    # service = get_app()
    click.echo('Running scan...')
    if type_ == 'sast':
        command = 'docker run --env SNYK_TOKEN --rm --volume $(pwd):/app ' \
            'snyk/snyk:python snyk code test'
        click.secho(command, fg='green')
        run(command)
    if type_ == 'dependencies':
        command = 'docker run --env SNYK_TOKEN --rm --volume $(pwd):/app ' \
            'snyk/snyk:python snyk test'
        click.secho(command, fg='green')
        run(command)


# Start a ToL service
@cli.command()
@click.option('--ui/--no-ui', default=True, help='build the UI container')
@click.option('--db/--no-db', default=True, help='build the DB container')
@click.option('--api/--no-api', default=True, help='build the API container')
@click.pass_context
def up(ctx, ui, db, api):
    env_file = ctx.parent.params['env_file']
    service = get_app()
    click.echo(f'Starting {service}...')
    containers = []
    if ui:
        containers.append(f'{service}-ui')
    if db:
        containers.append(f'{service}-db')
    if api:
        containers.append(f'{service}-api')
    command = f'docker compose --env-file {env_file} up --build --detach ' \
        + ' '.join(containers)
    click.secho(command, fg='green')
    run(command)
    if api:
        click.secho('API: ' + ' '.join(get_container_urls(f'{service}-api')), fg='yellow')
    if ui:
        click.secho('UI: ' + ' '.join(get_container_urls(f'{service}-ui', protocol='https')),
                    fg='yellow')


# Log a ToL service
@cli.command()
@click.option('--ui/--no-ui', default=True, help='build the UI container')
@click.option('--db/--no-db', default=True, help='build the DB container')
@click.option('--api/--no-api', default=True, help='build the API container')
@click.pass_context
def log(ctx, ui, db, api):
    env_file = ctx.parent.params['env_file']
    service = get_app()
    containers = []
    if ui:
        containers.append(f'{service}-ui')
    if db:
        containers.append(f'{service}-db')
    if api:
        containers.append(f'{service}-api')
    command = f'docker compose --env-file {env_file} logs --tail=0 --follow ' \
        + ' '.join(containers)
    click.secho(command, fg='green')
    run(command)


# Stop a ToL service
@cli.command()
@click.pass_context
def down(ctx):
    env_file = ctx.parent.params['env_file']
    service = get_app()
    click.echo(f'Stopping {service}...')
    command = f'docker compose  --env-file {env_file} down'
    click.secho(command, fg='green')
    run(command)


# Prune
@cli.command()
def prune():
    click.echo('Pruning all Docker containers, volumes, etc...')
    command = 'docker system prune -af'
    click.secho(command, fg='green')
    run(command)
    command = 'docker volume prune -f'
    click.secho(command, fg='green')
    run(command)


# Restore a database from backup
@cli.command()
@click.pass_context
def restore(ctx):
    env_file = ctx.parent.params['env_file']
    service = get_app()
    click.echo('Restoring database...')
    command = (
        f'docker compose --env-file {env_file} run --rm {service}-dbutils'
        ' python3 run.py restore'
    )
    click.secho(command, fg='green')
    run(command)


# The Alembic group
@cli.group
@click.pass_context
def alembic(ctx):
    pass


# Run an Alembic upgrade on the databse
@alembic.command()
@click.pass_context
def upgrade(ctx):
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Running alembic upgrade...')
    command = f'docker compose build {service}-api && docker compose --env-file {env_file} ' \
        + f'run --rm {service}-alembic alembic upgrade head'
    click.secho(command, fg='green')
    run(command)


# Create a new database migration
@alembic.command()
@click.option('--message', required=True, help='migration message')
@click.pass_context
def migration(ctx, message):
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Creating alembic migration...')
    command = f'docker compose build {service}-api && docker compose --env-file {env_file} ' \
        + f'run --rm {service}-alembic alembic revision -m "{message}"'
    click.secho(command, fg='green')
    run(command)


# Merge heads
@alembic.command()
@click.pass_context
def merge(ctx):
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Merging heads...')
    command = f'docker compose build {service}-api && docker compose --env-file {env_file} ' \
        + f'run --rm {service}-alembic alembic merge heads -m "merge heads"'
    click.secho(command, fg='green')
    run(command)


# Run tests
@cli.command()
@click.option('--type', 'type_', default='unit',
              type=click.Choice(['unit', 'system', 'integration', 'ui', 'playwright']),
              help='type of test')
@click.pass_context
def test(ctx, type_):
    env_file = ctx.parent.params['env_file']
    service = get_app()

    click.echo('Running tests...')
    if type_ == 'unit':
        docker_compose_entry = f'{service}-python-unit-test'
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} run --rm {docker_compose_entry} '
            f'sh -c "[ -d unit ] && pytest -v unit || echo \'No unit tests found\'"'
        )
    if type_ == 'system':
        docker_compose_entry = f'{service}-python-system-test'
        db_entry = f'{service}-python-db'
        uuid_prefix = uuid4().hex
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} up -d {db_entry} && '
            f'UUID_PREFIX={uuid_prefix} docker compose --env-file {env_file} '
            f'run --rm --build {docker_compose_entry} '
            f'sh -c "[ -d system ] && pytest -vvvx system || echo \'No system tests found\'"'
        )
    if type_ == 'integration':
        docker_compose_entry = f'{service}-python-integration-test'
        uuid_prefix = uuid4().hex
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'UUID_PREFIX={uuid_prefix} docker compose --env-file {env_file} '
            f'run --rm --build {docker_compose_entry} '
            f'sh -c "[ -d system ] && pytest -vvvx integration || '
            'echo \'No integration tests found\'"'
        )
    if type_ == 'ui':
        docker_compose_entry = f'{service}-ui-test'
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} run --rm {docker_compose_entry} '
            f'npm run test'
        )
    if type_ == 'playwright':
        docker_compose_entry = f'{service}-playwright-test'
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} run --rm {docker_compose_entry} '
            f'npx playwright test'
        )
    click.secho(command, fg='green')
    run(command)


# Run flow
@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.pass_context
def flow(ctx, filename):
    entry = f'{get_app()}-flow'
    env_file = ctx.parent.params['env_file']
    click.echo('Running flow...')
    command = (
        f'docker compose --env-file {env_file} run --rm --build '
        f'{entry} python3 /opt/prefect/flows/{filename}'
    )
    click.secho(command, fg='green')
    run(command)


# Data
@cli.command()
@click.option('--source', default='portal',
              type=click.Choice(['portal', 'goat', 'grit', 'sts', 'tolid', 'tolqc', 'workflows']),
              help='source DataSource')
@click.option('--operation', default='list',
              type=click.Choice(['list']),
              help='operation to run')
@click.option('--type', 'type_', required=True,
              help='object type')
@click.option('--filter', 'filter_', default=None,
              help='filter')
@click.option('--fields', default='',
              help='fields to output')
@click.option('--converter', default=None,
              help='converter function')
@click.option('--output', default='ndjson',
              type=click.Choice(['ndjson', 'tsv']),
              help='output type')
@click.pass_context
def data(ctx, source, operation, type_, filter_, fields, converter, output):
    env_file = ctx.parent.params['env_file']
    if os.path.exists(env_file):
        load_dotenv(ctx.parent.params['env_file'])
    module = importlib.import_module(f'tol.sources.{source}')
    class_ = getattr(module, source)
    ds = class_()
    f = DataSourceFilter()
    if filter_ is not None:
        try:
            provided_filter = json.loads(filter_)
            f.and_ = provided_filter['and_'] if 'and_' in provided_filter else {}
        except json.JSONDecodeError:
            pass
    if operation == 'list':
        objs = ds.get_list(type_, object_filters=f)
    if converter is not None:
        module = importlib.import_module('tol.flows.converters')
        class_ = getattr(module, converter)
        objs = class_(ds.data_object_factory).convert_iterable(objs)
    if output == 'tsv':
        output_tsv(objs, fields.split(',') if fields else [])
    if output == 'ndjson':
        output_json(objs, fields.split(',') if fields else [])


def output_tsv(objs, fields):
    for i, obj in enumerate(objs):
        if i == 0:
            if len(fields) == 0:
                fields = obj.attributes.keys()
            click.echo('\t'.join(fields))

        click.echo('\t'.join(
            str(obj.get_field_by_name(field))
            for field in fields
        ))


def output_json(objs, fields):
    """
    This is a very simple implementation. It doesn't yet handle relationships.
    """
    def datetime_handler(x):
        if isinstance(x, datetime.datetime):
            return x.isoformat()
        raise TypeError('Unknown type')

    for obj in objs:
        click.echo(json.dumps(
            {
                'id': obj.id,
                **obj.attributes
            },
            default=datetime_handler)
        )


def get_app():
    return os.path.basename(os.getcwd())


def run(command):
    try:
        subprocess.run(
            ['bash', '-i', '-c', command]
        ).check_returncode()
    except subprocess.CalledProcessError as e:
        exit(e.returncode)


def run_capture(command):
    s = subprocess.run(['bash', '-i', '-c', command], check=True, capture_output=True)
    return s.stdout.decode('utf-8')


def get_container_ids(name_prefix):
    ids = []
    output = run_capture('docker container ls')
    for line in output.split('\n'):
        if re.search(name_prefix, line):
            ids.append(line.split()[0])
    return ids


def get_container_urls(name_prefix, protocol='http'):
    urls = []
    container_ids = get_container_ids(name_prefix)
    for container_id in container_ids:
        if container_id != '':
            mapping = run_capture(f'docker container port {container_id}')
            if mapping != '':
                urls.append(f'{protocol}://' + mapping.split()[2])
    return urls
