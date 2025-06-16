# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
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
        to_one = {}
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
                    attributes['habitat'] = s.location.habitat

            attributes['col_date'] = self.__sanitise_date_field(s.col_date)
            attributes['original_collection_date'] = \
                self.__sanitise_date_field(s.original_collection_date)
            attributes['pre_date'] = self.__sanitise_date_field(s.pre_date)
            if 'gal' in s.to_one_relationships:
                if s.gal is not None:
                    attributes['gal_name'] = s.gal.name
                    attributes['gal_abbreviation'] = s.gal.abbreviation
            if 'preservation_approach' in s.to_one_relationships:
                if s.preservation_approach is not None:
                    attributes['preservation_approach'] = s.preservation_approach.approach
            if 'preservative_solution' in s.to_one_relationships:
                if s.preservative_solution is not None:
                    attributes['preservative_solution'] = s.preservative_solution.solution
            if 'collection_method' in s.to_one_relationships:
                if s.collection_method is not None:
                    attributes['collection_method_desc'] = s.collection_method.method
            if 'specimen' in s.to_one_relationships:
                if s.specimen is not None:
                    to_one['specimen'] = self._data_object_factory(
                        'specimen',
                        s.specimen.id
                    )
            if 'sampleset' in s.to_one_relationships:
                if s.sampleset is not None:
                    to_one['sampleset'] = self._data_object_factory(
                        'sampleset',
                        s.sampleset.id
                    )
            if 'manifest' in s.to_one_relationships:
                if s.manifest is not None:
                    to_one['manifest'] = self._data_object_factory(
                        'manifest',
                        s.manifest.id
                    )
            if 'tissue_size' in s.to_one_relationships:
                if s.tissue_size is not None:
                    attributes['tissue_size'] = s.tissue_size.size
            if 'sample_export_options' in s.to_one_relationships:
                if s.sample_export_options is not None:
                    attributes['lab_work_category'] = s.sample_export_options.display_name
            if 'storage_rack' in s.to_one_relationships:
                if s.storage_rack is not None:
                    attributes['location'] = s.storage_rack.freezer_tray.id
            # Make tolid a relationship
            if s.public_name is not None and s.public_name != '':
                to_one['tolid'] = self._data_object_factory(
                    'tolid',
                    s.public_name
                )
                attributes['public_name'] = None

            person_attributes = {}
            for sp in s.sample_persons:
                person_attributes[f'{sp.action.lower()}_name'] = sp.person.fullname

            ext_id_attributes = {}
            for ext_id in s.ext_ids:
                ext_id_attributes[f'{ext_id.ext_id_type.lower()}'] = ext_id.value

            sample_species_attributes = {}
            for ss in s.sample_species:
                if ss.target_or_symbiont == 'TARGET':
                    sample_species_attributes, sample_species_to_one = \
                        self.__convert_sample_species(ss)

        except DataSourceError:
            print(f'Problem with sample {s.id}')

        ret = self._data_object_factory(
            'sample',
            s.id,
            attributes=(
                attributes
                | person_attributes
                | sample_species_attributes
                | ext_id_attributes
            ),
            to_one=to_one | sample_species_to_one
        )
        yield ret

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

    def __convert_sample_species(self, data_object: DataObject) -> Iterable[DataObject]:
        organism_parts = []
        for ssop in data_object.sample_species_organism_parts:
            organism_parts.append(ssop.organism_part.name)

        return {
            'lifestage':
                data_object.lifestage.name
                if data_object.lifestage is not None else None,
            'strain':
                data_object.strain.name
                if data_object.strain is not None else None,
            'sex':
                data_object.sex.name
                if data_object.sex is not None else None,
            'organism_part': organism_parts
        }, {
            'species': self._data_object_factory(
                'species',
                data_object.species.id
            )
        }
