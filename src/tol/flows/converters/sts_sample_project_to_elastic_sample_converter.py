# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import re
from typing import Iterable

from dateutil import parser as dateutil_parser

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    DataSourceError
)


class StsSampleProjectToElasticSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        # The project (note this is adding to a list)
        s = data_object.sample
        attributes = {
            'project': [data_object.project.id],
            'programme': [data_object.project.programme],
            **s.attributes
        }
        try:
            if 'location' in s.to_one_relationships:
                if s.location is not None:
                    location = self.__split_location(s.location.location)
                    if location is not None:
                        attributes['collection_country'] = location['country']
                        attributes['collection_locality'] = location['locality']
                    attributes['latitude'] = s.location.lat
                    attributes['longitude'] = s.location.long
                    attributes['elevation'] = s.location.elevation
                    attributes['depth'] = s.location.depth

            attributes['col_date'] = self.__sanitise_date_field(s.col_date)
            attributes['original_collection_date'] = \
                self.__sanitise_date_field(s.original_collection_date)
            attributes['pre_date'] = self.__sanitise_date_field(s.pre_date)
            if 'gal' in s.to_one_relationships:
                if s.gal is not None:
                    attributes['gal_name'] = s.gal.name
                    attributes['gal_abbreviation'] = s.gal.abbreviation
            if 'specimen' in s.to_one_relationships:
                if s.specimen is not None:
                    attributes['specimen'] = {'id': s.specimen.id}
            if 'sampleset' in s.to_one_relationships:
                if s.sampleset is not None:
                    attributes['sampleset_id'] = s.sampleset.id
            # Make tolid a relationship
            if s.public_name is not None and s.public_name != '':
                attributes['tolid'] = {'id': s.public_name}
                attributes['public_name'] = None
        except DataSourceError:
            print(f'Problem with sample {s.id}')

        ret = self._data_object_factory(
            'sample',
            s.id,
            attributes=attributes
        )
        return iter([ret])

    def __sanitise_date_field(self, date_field: str) -> datetime.datetime:
        if date_field is None or date_field == '':
            return None
        try:
            parsed_date = dateutil_parser.parse(date_field, fuzzy=False)
            return parsed_date
        except ValueError:
            return None

    def __split_location(self, location: str) -> dict[str, str]:
        if location is None:
            return None
        splits = re.split(r'\s*\|\s*', location)
        return {
            'country': splits[0],
            'locality': ' | '.join(splits[1:])
        }
