# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

def generate_flattened_type(type_, **kwargs):
    """A generic method for getting a 'flat' generator of benchling
    types (i.e. one by one) from a list endpoint, e.g. assay_results
    or containers."""
    generator = type_.list(**kwargs)
    for page in generator:
        yield from page


def generate_workflow_tasks(benchling, **kwargs):
    return generate_flattened_type(
        benchling.workflow_tasks,
        **kwargs
    )


def generate_workflow_outputs(benchling, **kwargs):
    return generate_flattened_type(
        benchling.workflow_outputs,
        **kwargs
    )


def generate_assay_results(benchling, **kwargs):
    return generate_flattened_type(
        benchling.assay_results,
        **kwargs
    )


def generate_containers(benchling, **kwargs):
    return generate_flattened_type(
        benchling.containers,
        **kwargs
    )


def generate_boxes(benchling, **kwargs):
    return generate_flattened_type(
        benchling.boxes,
        **kwargs
    )


def generate_custom_entities(benchling, **kwargs):
    return generate_flattened_type(
        benchling.custom_entities,
        **kwargs
    )
