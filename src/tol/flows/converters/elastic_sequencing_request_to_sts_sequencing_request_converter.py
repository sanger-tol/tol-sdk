# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSequencingRequestToStsSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        submission_date = datetime.fromtimestamp(0)
        if 'benchling_completion_date' in data_object.attributes and \
                data_object.benchling_completion_date is not None:
            submission_date = data_object.benchling_completion_date

        ret = self._data_object_factory(
            'sequencing_request',
            data_object.id,
            attributes={
                'fluidx_id': data_object.benchling_fluidx_id,
                'platform': data_object.benchling_sequencing_platform.upper(),
                'submission_date': submission_date
            })
        return iter([ret])
