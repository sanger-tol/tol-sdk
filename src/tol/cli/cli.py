# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import re
import subprocess
from uuid import uuid4

import click


@click.group()
@click.option(
    '--env-file', default='.env.dev',
    type=click.Path(exists=True), help='set a custom .env file'
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
    command = f'docker compose --env-file {env_file} run {service}-dbutils python3 run.py restore'
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
        + f'run {service}-alembic alembic merge heads -m "merge heads"'
    click.secho(command, fg='green')
    run(command)


# Run tests
@cli.command()
@click.option('--type', 'type_', default='unit',
              type=click.Choice(['unit', 'system', 'integration']),
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
            f'docker compose --env-file {env_file} run {docker_compose_entry} '
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
            f'run --build {docker_compose_entry} '
            f'sh -c "[ -d system ] && pytest -v system || echo \'No system tests found\'"'
        )
    if type_ == 'integration':
        click.echo('Integration tests are not supported at this time.')
        return
    click.secho(command, fg='green')
    run(command)


# Run flow
@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--version', required=True, help='flows-base version', default='1.2.27')
@click.pass_context
def flow(ctx, filename, version):
    env_file = ctx.parent.params['env_file']
    click.echo('Running flow...')
    flow_name = os.path.basename(filename)
    command = (
        f'docker run --env-file {env_file} -v '
        '$(pwd)/app/flows:/flows '
        f'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/flows-base:{version} python3 '
        f'/flows/{flow_name}'
    )
    click.secho(command, fg='green')
    run(command)


def get_app():
    return os.path.basename(os.getcwd())


def run(command):
    return_code = os.system(command)
    if return_code != 0:
        exit(return_code)


def run_capture(command):
    list_command = command.split()
    s = subprocess.run(list_command, check=True, capture_output=True)
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
