# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import importlib
import json
import os
import re
import shlex
import subprocess

import click

from dotenv import load_dotenv

from ..core import (
    DataSourceFilter
)


@click.group()
@click.option(
    '--env-file',
    default='.env.dev',
    type=click.Path(),
    help='Use a custom environment file.',
    show_default=True,
)
def cli(env_file):
    pass


@cli.command()
@click.option(
    '--type',
    'type_',
    default='python',
    type=click.Choice(['python', 'license', 'ui', 'ui-fix']),
    help='Type of lint.',
    show_default=True,
)
def lint(type_):
    """
    Run linting.
    """

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


@cli.command()
@click.option(
    '--type',
    'type_',
    default='sast',
    type=click.Choice(['sast', 'dependencies']),
    help='Type of scan to run.',
    show_default=True,
)
def scan(type_):
    """
    Perform a Snyk security scan.
    """
    token = os.getenv('SNYK_TOKEN')
    if token is None:
        click.secho('SNYK_TOKEN environment variable must be set', fg='red')
        return
    # service = get_app()
    click.echo('Running scan...')
    snyc_common = 'docker run --env SNYK_TOKEN --rm --volume $(pwd):/app'
    if type_ == 'sast':
        command = f'{snyc_common} snyk/snyk:python snyk code test'
    elif type_ == 'dependencies':
        command = f'{snyc_common} snyk/snyk:python snyk test'
    click.secho(command, fg='green')
    run(command)


@cli.command()
@click.option('--ui/--no-ui', default=True, help='Build and run the UI container.')
@click.option('--db/--no-db', default=True, help='Build and run the DB container.')
@click.option('--api/--no-api', default=True, help='Build and run the API container.')
@click.pass_context
def up(ctx, ui, db, api):
    """
    Start ToL services.
    """
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
    command = f'docker compose --env-file {env_file} up --build --detach ' + ' '.join(containers)
    click.secho(command, fg='green')
    run(command)
    if api:
        click.secho('API: ' + ' '.join(get_container_urls(f'{service}-api')), fg='yellow')
    if ui:
        click.secho(
            'UI: ' + ' '.join(get_container_urls(f'{service}-ui', protocol='https')), fg='yellow'
        )


@cli.command()
@click.option('--ui/--no-ui', default=True, help='Log the UI container.')
@click.option('--db/--no-db', default=True, help='Log the DB container.')
@click.option('--api/--no-api', default=True, help='Log the API container.')
@click.pass_context
def log(ctx, ui, db, api):
    """
    Log ToL services.
    """
    env_file = ctx.parent.params['env_file']
    service = get_app()
    containers = []
    if ui:
        containers.append(f'{service}-ui')
    if db:
        containers.append(f'{service}-db')
    if api:
        containers.append(f'{service}-api')
    command = (
        f'docker compose --env-file {env_file} logs --tail=0 --follow '
        + ' '.join(containers)
    )
    click.secho(command, fg='green')
    run(command)


@cli.command()
@click.pass_context
def down(ctx):
    """
    Stop ToL services.
    """
    env_file = ctx.parent.params['env_file']
    service = get_app()
    click.echo(f'Stopping {service}...')
    command = f'docker compose  --env-file {env_file} down'
    click.secho(command, fg='green')
    run(command)


@cli.command()
def prune():
    """
    Prune all non-running Docker containers and volumes.
    """
    click.echo('Pruning all Docker containers, volumes, etc...')
    command = 'docker system prune -af'
    click.secho(command, fg='green')
    run(command)
    command = 'docker volume prune -f'
    click.secho(command, fg='green')
    run(command)


@cli.command()
@click.pass_context
def restore(ctx):
    """
    Restore a database from backup.
    """
    env_file = ctx.parent.params['env_file']
    service = get_app()
    click.echo('Restoring database...')
    command = (
        f'docker compose --env-file {env_file} run --rm {service}-dbutils'
        ' python3 run.py restore'
    )
    click.secho(command, fg='green')
    run(command)


@cli.group
@click.pass_context
def alembic(ctx):
    """
    Run Alembic.
    """


@alembic.command()
@click.pass_context
def upgrade(ctx):
    """
    Run migrations on the database.
    """
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Running alembic upgrade...')
    command = (
        f'docker compose build {service}-api && docker compose --env-file {env_file}'
        f' run --rm {service}-alembic alembic upgrade head'
    )
    click.secho(command, fg='green')
    run(command)


@alembic.command()
@click.option('--message', required=True, help='migration message')
@click.pass_context
def migration(ctx, message):
    """
    Create a new database migration.
    """
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Creating alembic migration...')
    command = (
        f'docker compose build {service}-api && docker compose --env-file {env_file}'
        f' run --rm {service}-alembic alembic revision -m "{message}"'
    )
    click.secho(command, fg='green')
    run(command)


@alembic.command()
@click.pass_context
def merge(ctx):
    """
    Merge heads.
    """
    env_file = ctx.parent.parent.params['env_file']
    service = get_app()
    click.echo('Merging heads...')
    command = (
        f'docker compose build {service}-api && docker compose --env-file {env_file}'
        f' run --rm {service}-alembic alembic merge heads -m "merge heads"'
    )
    click.secho(command, fg='green')
    run(command)


@cli.command(
    context_settings={
        # For passing unknown options to pytest
        'ignore_unknown_options': True,
    }
)
@click.option(
    '--type',
    'type_',
    default='unit',
    type=click.Choice(
        [
            'unit',
            'system',
            'integration',
            'ui',
            'playwright',
        ]
    ),
    help='Type of test to run.',
    show_default=True,
)
@click.argument(
    'pytest_options',
    nargs=-1,
    type=click.UNPROCESSED,
)
@click.pass_context
def test(ctx, type_, pytest_options):
    """
    Run tests. Any unrecognised options on the command line are accumulated in
    `PYTEST_OPTIONS` and passed to `pytest` for the "unit", "system"
    and "integration" test types.

    For example, to run just the system test `my_test`:

       tol test --type system -k my_test
    """
    env_file = ctx.parent.params['env_file']
    service = get_app()

    click.echo('Running tests...')
    if type_ in {'unit', 'system', 'integration'}:
        verbosity = '-v' if type_ == 'unit' else '-vv'
        # shlex will correctly re-quote any quoted arguments from the command
        # line:
        pytest_cmd = shlex.join(['pytest', verbosity, type_, *pytest_options])
        pytest_sh = (
            f'sh -c "if [ -d {type_} ]; then {pytest_cmd};'
            f' else echo \'No {type_} tests found\'; fi"'
        )
        if type_ == 'unit':
            docker_compose_entry = f'{service}-python-unit-test'
            command = (
                f'docker compose build {docker_compose_entry}'
                f' && docker compose --env-file {env_file}'
                f' run --rm {docker_compose_entry} {pytest_sh}'
            )
        elif type_ == 'system':
            docker_compose_entry = f'{service}-python-system-test'
            db_entry = f'{service}-python-db'
            command = (
                f'docker compose build {docker_compose_entry}'
                f' && docker compose --env-file {env_file} up -d {db_entry}'
                f' && docker compose --env-file {env_file}'
                f' run --rm --build {docker_compose_entry} {pytest_sh}'
            )
        elif type_ == 'integration':
            docker_compose_entry = f'{service}-python-integration-test'
            command = (
                f'docker compose build {docker_compose_entry}'
                f' && docker compose --env-file {env_file}'
                f' run --rm --build {docker_compose_entry} {pytest_sh}'
            )
    elif type_ == 'ui':
        docker_compose_entry = f'{service}-ui-test'
        command = (
            f'docker compose build {docker_compose_entry}'
            f' && docker compose --env-file {env_file}'
            f' run --rm {docker_compose_entry} npm run test'
        )
    elif type_ == 'playwright':
        docker_compose_entry = f'{service}-playwright-test'
        command = (
            f'docker compose build {docker_compose_entry}'
            f' && docker compose --env-file {env_file} '
            f' run --rm {docker_compose_entry} npx playwright test'
        )
    click.secho(command, fg='green')
    run(command)


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.pass_context
def flow(ctx, filename):
    """
    Run a flow.
    """
    entry = f'{get_app()}-flow'
    env_file = ctx.parent.params['env_file']
    click.echo('Running flow...')
    command = (
        f'docker compose --env-file {env_file} run --rm --build '
        f'{entry} python3 /opt/prefect/flows/{filename}'
    )
    click.secho(command, fg='green')
    run(command)


@cli.command()
@click.option(
    '--source',
    default='portal',
    type=click.Choice(
        [
            'portal',
            'goat',
            'grit',
            'sts',
            'tolid',
            'tolqc',
            'workflows',
        ]
    ),
    help='Source DataSource',
    show_default=True,
)
@click.option(
    '--operation',
    default='list',
    type=click.Choice(['list']),
    help='Operation to run.',
    show_default=True,
)
@click.option(
    '--type',
    'type_',
    required=True,
    help='Object type.',
)
@click.option(
    '--filter',
    'filter_',
    default=None,
    help='Filter to apply.',
)
@click.option(
    '--fields',
    default='',
    help='Fields to output.',
)
@click.option(
    '--converter',
    default=None,
    help='Converter function,',
)
@click.option(
    '--output',
    default='ndjson',
    type=click.Choice(
        ['ndjson', 'tsv'],
    ),
    help='Format of the output.',
    show_default=True,
)
@click.pass_context
def data(ctx, source, operation, type_, filter_, fields, converter, output):
    """
    Fetch data from a DataSource.
    """
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
