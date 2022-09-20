# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from prefect import task
from prefect.engine.signals import FAIL
from datetime import timedelta

from .. import (
    get_datetime_setting,
    update_datetime_setting,
    sts_requests
)
from .logger import get_prefect_logger
from ..eln import (
    get_benchling_instance,
    generate_assay_results
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
            container_eln_id = assay_result.fields.to_dict()["sample_tube"]["displayValue"]
            sanger_sample_id = assay_result.fields.to_dict()["sanger_sample_id"]["value"]
            ret[container_eln_id] = sanger_sample_id
    print("Found this many Sanger Sample IDs: " + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def add_sanger_sample_ids(submissions, eln_sanger_sample_id_schema_id):
    container_ids = [d['container_eln_id'] for d in submissions]
    sanger_sample_ids = get_sanger_sample_ids_for_container_list(
        container_ids,
        eln_sanger_sample_id_schema_id)
    ret = []
    for submission in submissions:
        if submission["fluidx_id"] in sanger_sample_ids:
            ret.append({**submission,
                        'sanger_sample_id': sanger_sample_ids[submission["fluidx_id"]]})
        else:
            get_prefect_logger().warning("Cannot find Sanger Sample ID for tube: "
                                         + submission["fluidx_id"])
    get_prefect_logger().info("Total number of viable submissions: " + str(len(ret)))
    return ret


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def post_sequencing_requests_to_sts(submissions, platform):
    updated_count = 0
    for submission in submissions:
        submission_date = submission["submission_date"]
        if submission_date is None:
            get_prefect_logger().warning(submission["fluidx_id"]
                                         + " does not have a submission date")
            submission_date = "1970-01-01"
        payload = {"platform": platform,
                   "fluidx_id": submission["fluidx_id"],
                   "sample_ref": submission["sanger_sample_id"],
                   "submit_date": submission_date + " 00:00:00"}
        r = sts_requests.post(
            '/sequencing-requests',
            json=payload
        )
        if r.ok:
            updated_count += 1
        else:
            get_prefect_logger().warning(
                f"A sample failed with code {r.status_code}, "
                f"and response {r.json()}, "
                f"containing data: {payload}"
            )
    get_prefect_logger().info("Total number of sequencing requests posted: " + str(updated_count))
    return True


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def get_lastrun_datetime(key):
    lastrun_datetime = get_datetime_setting(key)
    if lastrun_datetime is None:
        get_prefect_logger().error(
            'Could not load the datetime of last run.'
        )
        raise FAIL()
    get_prefect_logger().info(f"Last run on {lastrun_datetime}")
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
    get_prefect_logger().info(f"Updated last run date to {new_datetime}")
    return True
