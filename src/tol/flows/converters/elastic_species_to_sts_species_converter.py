# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSpeciesToStsSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None:
            legislation = {}
            for att in ['echabs92', 'habreg_2017', 'marhabreg-2017',
                        'waca_1981', 'isb_wildlife_act_1976',
                        'protection_of_badgers_act_1992']:
                att_value = getattr(data_object, f'goat_{att}')
                if att_value is not None:
                    legislation[att] = att_value
            attributes = {
                'legislation': json.dumps(legislation, default=str)
                if legislation != {} else None,
                'family_representative': data_object.goat_family_representative,
                'prefix': data_object.tolid_prefix
            }
            # Don't override the genome size as it may be already set
            if data_object.goat_genome_size is not None:
                attributes['genome_size'] = data_object.goat_genome_size
            yield self._data_object_factory(
                'species',
                data_object.id,
                attributes=attributes
            )
