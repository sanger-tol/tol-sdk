# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

from ..core import DataObject


class FlowRunObject(DataObject):
    """
    Contains fields relevant for a `Flow Run`
    in prefect.

    Used only for type hints.
    """

    flow_name: str
    deployment_name: str

    name: Optional[str]
    tags: Optional[list[str]]
    state: Optional[str]
    idempotency_key: Optional[str]
    parameters: Optional[dict[str, Any]]
