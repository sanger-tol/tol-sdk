# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import re
import subprocess

import click


@click.group()
def cli():
    pass


# Lint
@cli.command()
@click.option('--type', 'type_', default='python', type=click.Choice(['python', 'license']),
              help='type of test')
def lint(type_):
    # service = get_app()
    click.echo('Running lint...')
    if type_ == 'license':
        command = 'docker run --rm --volume $(pwd):/data fsfe/reuse lint'
        click.secho(command, fg='green')
        run(command)
    if type_ == 'python':
        linter = 'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/lint:1.0.0'
        command = f'docker run --rm --volume $(pwd):/project {linter}'
        click.secho(command, fg='green')
        run(command)


# Start a ToL service
@cli.command()
@click.option('--ui/--no-ui', default=True, help='build the UI container')
@click.option('--db/--no-db', default=True, help='build the DB container')
@click.option('--api/--no-api', default=True, help='build the API container')
@click.option('--env-file', default='.env.dev', help='set a custom .env file')
def up(ui, db, api, env_file):
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
        click.secho('API: ' + get_container_url(f'{service}-api'), fg='yellow')
    if ui:
        click.secho('UI: ' + get_container_url(f'{service}-ui'), fg='yellow')


# Stop a ToL service
@cli.command()
def down():
    service = get_app()
    click.echo(f'Stopping {service}...')
    command = 'docker compose down'
    click.secho(command, fg='green')
    run(command)


# Restore a database from backup
@cli.command()
def restore():
    service = get_app()
    click.echo('Restoring database...')
    command = f'docker compose --env-file .env.dev run {service}-dbutils python3 run.py restore'
    click.secho(command, fg='green')
    run(command)


# Run an Alembic upgrade on the databse
@cli.command()
@click.option('--env-file', default='.env.dev', help='set a custom .env file')
def alembic(env_file):
    service = get_app()
    click.echo('Running alembic upgrade...')
    command = f'docker compose build {service}-api && docker compose --env-file {env_file} ' \
        + f'run {service}-alembic alembic upgrade head'
    click.secho(command, fg='green')
    run(command)


# Create a new database migration
@cli.command()
@click.option('--message', required=True, help='migration message')
@click.option('--env-file', default='.env.dev', help='set a custom .env file')
def migration(message, env_file):
    service = get_app()
    click.echo('Creating alembic migration...')
    command = f'docker compose build {service}-api && docker compose --env-file {env_file} ' \
        + f'run {service}-alembic alembic revision -m "{message}"'
    click.secho(command, fg='green')
    run(command)


# Run tests
@cli.command()
@click.option('--env-file', default='.env.dev', help='set a custom .env file')
@click.option('--type', 'type_', default='unit',
              type=click.Choice(['unit', 'system', 'integration']),
              help='type of test')
def test(env_file, type_):
    service = get_app()
    click.echo('Running tests...')
    if type_ == 'unit':
        docker_compose_entry = f'{service}-python-unit-test'
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} run {docker_compose_entry}'
        )
    if type_ == 'system':
        docker_compose_entry = f'{service}-python-system-test'
        db_entry = f'{service}-python-db'
        command = (
            f'docker compose build {docker_compose_entry} && '
            f'docker compose --env-file {env_file} up -d {db_entry} && '
            f'docker compose --env-file {env_file} run {docker_compose_entry}'
        )
    if type_ == 'integration':
        click.echo('Integration tests are not supported at this time.')
        return
    click.secho(command, fg='green')
    run(command)


# Run flow
@cli.command()
@click.option('--env-file', default='.env.dev', help='set a custom .env file')
@click.argument('filename', type=click.Path(exists=True))
def flow(env_file, filename):
    click.echo('Running flow...')
    flow_name = os.path.basename(filename)
    command = (
        f'docker run --env-file {env_file} -v '
        '$(pwd)/app/flows:/flows '
        'gitlab-registry.internal.sanger.ac.uk/tol/tol-core/flows-base:1.1.0 python3 '
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


def get_container_id(name):
    output = run_capture('docker container ls')
    for line in output.split('\n'):
        if re.search(name, line):
            id_ = line.split()[0]
    return id_


def get_container_url(name):
    url = ''
    container_id = get_container_id(name)
    if container_id != '':
        mapping = run_capture(f'docker container port {container_id}')
        if mapping != '':
            url = 'http://' + mapping.split()[2]
    return url
