# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolqcDataToElasticRunDataConverter(DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        target_attributes = {}
        target_to_one = {}

        target_attributes['tag_index'] = data_object.tag_index
        target_attributes['tag_sequence'] = data_object.tag1_id
        target_attributes['tag2_sequence'] = data_object.tag2_id
        target_attributes['manual_qc'] = data_object.lims_qc
        target_attributes['auto_qc'] = data_object.auto_qc
        target_attributes['qc'] = data_object.qc
        target_attributes['read_length_n50'] = data_object.read_length_n50
        target_attributes['bases'] = data_object.bases
        target_attributes['bases_a'] = data_object.bases_a
        target_attributes['bases_c'] = data_object.bases_c
        target_attributes['bases_g'] = data_object.bases_g
        target_attributes['bases_t'] = data_object.bases_t
        if data_object.library is not None \
                and data_object.library.library_type is not None:
            target_attributes['reporting_category'] = \
                data_object.library.library_type.reporting_category

        if data_object.run is not None:
            target_attributes['run'] = data_object.run.id
            target_attributes['position'] = data_object.run.element
            target_attributes['run_start'] = data_object.run.start
            target_attributes['run_complete'] = data_object.run.complete

            if data_object.run.platform is not None:
                target_attributes['instrument_model'] = data_object.run.platform.model

        if data_object.sample is not None:
            target_to_one['sequencing_request'] = self._data_object_factory(
                'sequencing_request',
                data_object.sample.id
            )
            if data_object.sample.specimen is not None:
                target_to_one['tolid'] = self._data_object_factory(
                    'tolid',
                    data_object.sample.specimen.id
                )
                if data_object.sample.specimen.supplied_name is not None:
                    target_to_one['specimen'] = self._data_object_factory(
                        'specimen',
                        data_object.sample.specimen.supplied_name
                    )
                if data_object.sample.specimen.accession is not None:
                    target_attributes['biospecimen_id'] = data_object.sample.specimen.accession.id
                if data_object.sample.specimen.species is not None:
                    target_to_one['species'] = self._data_object_factory(
                        'species',
                        data_object.sample.specimen.species.taxon_id
                    )

        if data_object.folder is not None:
            target_attributes['images'] = [
                {
                    'url':
                        f'{data_object.folder.folder_location.uri_prefix}'
                        f'/{data_object.folder.id}'
                        '/' + file.get('file', ''),
                    'caption': file.get('caption')
                }
                for file in data_object.folder.image_file_list
            ]

        ret = self._data_object_factory(
            'run_data',
            data_object.id,
            attributes=target_attributes,
            to_one=target_to_one
        )
        yield ret
