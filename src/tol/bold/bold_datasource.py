# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Callable, Iterable, Optional

from .client import BoldApiClient
from .converter import (
    BoldApiConverter
)
from ..core import DataObject, DataSource, DataSourceError
from ..core.operator import (
    DetailGetter
)


ClientFactory = Callable[[], BoldApiClient]
BoldConverterFactory = Callable[[], BoldApiConverter]


class BoldDataSource(
    DataSource,

    # the supported operators
    DetailGetter
):
    """
    A `DataSource` that connects to a remote BOLD API.

    Developers should likely use `create_bold_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        bold_converter_factory: BoldConverterFactory
    ) -> None:

        self.__client_factory = client_factory
        self.__lc_factory = bold_converter_factory
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'sample': {
                'processid': 'str',
                'record_id': 'str',
                'insdc_acs': 'str',
                'sampleid': 'str',
                'specimenid': 'int',
                'taxid': 'int',
                'short_note': 'str',
                'identification_method': 'str',
                'museumid': 'str',
                'fieldid': 'str',
                'collection_code': 'str',
                'processid_minted_date': 'datetime',
                'inst': 'str',
                'funding_src': 'str',
                'sex': 'str',
                'life_stage': 'str',
                'reproduction': 'str',
                'habitat': 'str',
                'collectors': 'str',
                'site_code': 'str',
                'specimen_linkout': 'str',
                'collection_event_id': 'str',
                'sampling_protocol': 'str',
                'tissue_type': 'str',
                'collection_date_start': 'datetime',
                'collection_time': 'str',
                'associated_taxa': 'str',
                'associated_specimens': 'str',
                'voucher_type': 'str',
                'notes': 'str',
                'taxonomy_notes': 'str',
                'collection_notes': 'str',
                'geoid': 'int',
                'marker_code': 'str',
                'kingdom': 'str',
                'phylum': 'str',
                'class': 'str',
                'order': 'str',
                'family': 'str',
                'subfamily': 'str',
                'tribe': 'str',
                'genus': 'str',
                'species': 'str',
                'subspecies': 'str',
                'taxon_name': 'str',
                'taxon_rank': 'str',
                'species_reference': 'str',
                'identified_by': 'str',
                'sequence_run_site': 'str',
                'nuc': 'str',
                'nuc_basecount': 'int',
                'sequence_upload_date': 'datetime',
                'bin_uri': 'str',
                'bin_created_date': 'datetime',
                'elev': 'int',
                'depth': 'int',
                'coord': 'List[int]',
                'coord_source': 'str',
                'coord_accuracy': 'str',
                'elev_accuracy': 'str',
                'depth_accuracy': 'str',
                'region': 'str',
                'sector': 'str',
                'site': 'str',
                'country_iso': 'str',
                'country/ocean': 'str',
                'province/state': 'str',
                'bold_recordset_code_arr': 'List[str]',
                'collection_date_end': 'datetime'
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        client = self.__client_factory()
        bold_response = client.get_detail(object_type, object_ids)
        bold_converter = self.__lc_factory()

        converted_objects, _ = bold_converter.convert_list(bold_response) \
            if bold_response is not None else ([], 0)
        yield from self.sort_by_id(converted_objects, object_ids)
