# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import timedelta

from prefect import task
from prefect.engine.signals import FAIL

from .logger import get_prefect_logger
from ..eln import (
    generate_assay_results,
    generate_containers,
    generate_custom_entities,
    generate_workflow_outputs,
    generate_workflow_tasks,
    get_benchling_instance,
    sanitise_value
)
from ..sts import (
    get_datetime_setting,
    sts_requests,
    update_datetime_setting,
)


def get_sanger_sample_ids_for_container_list(container_ids, eln_schema_id):
    benchling = get_benchling_instance()
    ret = {}
    # We can only get 20 at once
    for containers_page in [container_ids[i:i + 20] for i in range(0, len(container_ids), 20)]:
        assay_results_page = generate_assay_results(
            benchling,
            schema_id=eln_schema_id,
            storage_ids=containers_page
        )
        for assay_result in assay_results_page:
            container_fluidx_id = sanitise_value(
                assay_result.fields.to_dict()['sample_tube']['displayValue'])
            sanger_sample_id = sanitise_value(
                assay_result.fields.to_dict()['sanger_sample_id']['value'])
            ret[container_fluidx_id] = sanger_sample_id
    get_prefect_logger().info('Found this many Sanger Sample IDs: ' + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_sanger_sample_ids(submissions, eln_sanger_sample_id_schema_id):
    container_ids = [d['container_eln_id'] for d in submissions]
    sanger_sample_ids = get_sanger_sample_ids_for_container_list(
        container_ids,
        eln_sanger_sample_id_schema_id)
    ret = []
    for submission in submissions:
        if submission['fluidx_id'] in sanger_sample_ids:
            ret.append({**submission,
                        'sanger_sample_id': sanger_sample_ids[submission['fluidx_id']]})
        else:
            get_prefect_logger().warning('Cannot find Sanger Sample ID for tube: '
                                         + submission['fluidx_id'])
    get_prefect_logger().info('Total number of viable submissions: ' + str(len(ret)))
    return ret


def get_fluidx_ids_for_workflow_task_list(workflow_task_ids):
    benchling = get_benchling_instance()
    ret = {}
    # We can only get 20 at once
    for workflow_task_id_page in \
            [workflow_task_ids[i:i + 20] for i in range(0, len(workflow_task_ids), 20)]:
        workflow_tasks_page = generate_workflow_tasks(
            benchling,
            ids=workflow_task_id_page
        )
        for workflow_task in workflow_tasks_page:
            workflow_task_id = workflow_task.id
            fluidx_id = sanitise_value(
                workflow_task.fields.to_dict()['Sample Tube']['displayValue'])
            ret[workflow_task_id] = fluidx_id
    get_prefect_logger().info('Found this many FluidX IDs: ' + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_fluidx_ids(submissions):
    workflow_task_ids = [d['workflow_task_id'] for d in submissions]
    fluidx_ids = get_fluidx_ids_for_workflow_task_list(
        workflow_task_ids)
    ret = []
    for submission in submissions:
        if submission['workflow_task_id'] in fluidx_ids:
            ret.append({**submission,
                        'fluidx_id': fluidx_ids[submission['workflow_task_id']]})
        else:
            get_prefect_logger().warning('Cannot find Sanger Sample ID for workflow task: '
                                         + submission['workflow_task_id'])
    get_prefect_logger().info('Total number of viable submissions: ' + str(len(ret)))
    return ret


def get_created_dates_for_container_list(container_ids):
    benchling = get_benchling_instance()
    ret = {}
    # We can only get 20 at once
    for containers_page in [container_ids[i:i + 20] for i in range(0, len(container_ids), 20)]:
        container_results_page = generate_containers(
            benchling,
            ids=containers_page
        )
        for container in container_results_page:
            container_barcode = container.barcode
            created_date = container.created_at
            ret[container_barcode] = created_date.strftime('%Y-%m-%d %H:%M:%S')
    get_prefect_logger().info('Found this many container created dates: ' + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_container_dates(submissions):
    container_ids = [d['container_eln_id'] for d in submissions]
    container_dates = get_created_dates_for_container_list(
        container_ids)
    ret = []
    for submission in submissions:
        if submission['sanger_sample_id'] in container_dates:
            ret.append({**submission,
                        'submission_date': container_dates[submission['sanger_sample_id']]})
        else:
            get_prefect_logger().warning('Cannot find created date for tube: '
                                         + submission['sanger_sample_id'])
    get_prefect_logger().info('Total number of viable submissions: ' + str(len(ret)))
    return ret


def get_contents_for_container_list(container_ids):
    benchling = get_benchling_instance()
    ret = {}
    # We can only get 20 at once
    for containers_page in [container_ids[i:i + 20] for i in range(0, len(container_ids), 20)]:
        returned_page = generate_containers(
            benchling,
            ids=containers_page,
            archive_reason='ANY_ARCHIVED_OR_NOT_ARCHIVED'
        )
        for container in returned_page:
            if len(container.contents) > 0:
                container_fluidx_id = container.barcode
                entity_id = container.contents[0].entity.to_dict()['fields']['Tissue']['value']
                ret[container_fluidx_id] = entity_id
    get_prefect_logger().info('Found this many Entity IDs: ' + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_container_contents(submissions):
    container_ids = [d['container_eln_id'] for d in submissions]
    entity_ids = get_contents_for_container_list(
        container_ids)
    ret = []
    for submission in submissions:
        if submission['fluidx_id'] in entity_ids:
            ret.append({**submission,
                        'entity_id': entity_ids[submission['fluidx_id']]})
        else:
            get_prefect_logger().warning('Cannot find Entity ID for tube: '
                                         + submission['fluidx_id'])
    get_prefect_logger().info('Total number of containers with contents: ' + str(len(ret)))
    return ret


def get_sts_ids_for_entity_list(entity_ids):
    benchling = get_benchling_instance()
    ret = {}
    # We can only get 20 at once
    for entities_page in [entity_ids[i:i + 20] for i in range(0, len(entity_ids), 20)]:
        returned_page = generate_custom_entities(
            benchling,
            ids=entities_page,
            archive_reason='ANY_ARCHIVED_OR_NOT_ARCHIVED'
        )
        for entity in returned_page:
            entity_id = entity.id
            sts_id = entity.fields['STS ID'].value
            ret[entity_id] = sts_id
    get_prefect_logger().info('Found this many STS IDs: ' + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_entity_sts_ids(submissions):
    entity_ids = [d['entity_id'] for d in submissions]
    sts_ids = get_sts_ids_for_entity_list(
        entity_ids)
    ret = []
    for submission in submissions:
        if submission['entity_id'] in sts_ids:
            ret.append({**submission,
                        'sts_id': sts_ids[submission['entity_id']]})
        else:
            get_prefect_logger().warning('Cannot find STS ID for tube: '
                                         + submission['fluidx_id'])
    get_prefect_logger().info("Total number of containers with content parent's STS id: "
                              f'{len(ret)}')
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def post_ep_samples_to_sts(submissions):
    updated_count = 0
    for submission in submissions:
        submission_date = submission['submission_date']
        if submission_date is None:
            get_prefect_logger().warning(submission['fluidx_id']
                                         + ' does not have a submission date')
            submission_date = '1970-01-01 00:00:00'
        payload = {'fluidx_id': submission['fluidx_id'],
                   'sample_id': submission['sts_id'],
                   'type': 'DNA',
                   'extraction_date': submission_date}
        r = sts_requests.post(
            '/ep_samples/' + submission['fluidx_id'],
            json=payload
        )
        if r.ok:
            updated_count += 1
        else:
            get_prefect_logger().warning(
                f'A sample failed with code {r.status_code}, '
                f'and response {r.json()}, '
                f'containing data: {payload}'
            )
    get_prefect_logger().info('Total number of ep_samples posted: ' + str(updated_count))
    return True


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def get_lastrun_datetime(key):
    lastrun_datetime = get_datetime_setting(key)
    if lastrun_datetime is None:
        get_prefect_logger().error(
            'Could not load the datetime of last run.'
        )
        raise FAIL()
    get_prefect_logger().info(f'Last run on {lastrun_datetime}')
    return lastrun_datetime


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def update_lastrun_datetime(key, new_datetime, go):
    success = update_datetime_setting(
        key,
        new_datetime
    )
    if not success:
        get_prefect_logger().error(
            'Could not update the datetime for this run.'
        )
        raise FAIL()
    get_prefect_logger().info(f'Updated last run date to {new_datetime}')
    return True


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def get_new_lres_sample_data_from_eln(lastrun_datetime, schema_id):
    benchling = get_benchling_instance()
    lres_submissions = generate_workflow_outputs(
        benchling,
        schema_id=schema_id,
        modified_at='> ' + lastrun_datetime.isoformat('T')
    )
    lres_list = []
    for lres_submission in lres_submissions:
        tube_field = lres_submission.fields.to_dict()['Sample Tube ID']
        submission_date_field = lres_submission.fields.to_dict()['Submitted (Submission date)']
        submission_date = submission_date_field['value']
        if submission_date is not None:
            submission_date += ' 00:00:00'
        lres_list.append({'fluidx_id': sanitise_value(tube_field['displayValue']),
                          'container_eln_id': tube_field['value'],
                          'submission_date': submission_date})
    get_prefect_logger().info('Found this many LRES submissions: ' + str(len(lres_list)))
    return lres_list
