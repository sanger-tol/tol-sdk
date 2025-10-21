# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.bold.converter import (
    BoldApiConverter
)
from tol.bold.parser import DefaultParser
from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    return data_object


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> DataSource:

    mock_ds = create_autospec(DataSource, spec_set=True)

    mock_ds.attribute_types = attribute_types
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object

    return mock_ds


def _get_mock_ds_dict(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> dict[str, DataSource]:

    return DataSourceDict(
        _get_mock_data_source(attribute_types=attribute_types)
    )


class TestBoldApiConverter:
    """Tests `BoldApiConverter().convert()`"""

    def test_convert_sample(self):
        """Test the converter"""

        in_ = [
            {
                'processid': f'PROCESS{i}',
                'record_id': f'RECORD{i}',
                'insdc_acs': f'INSDC{i}',
                'sampleid': f'SAMPLE{i}',
                'specimenid': 1234 + i,
                'taxid': 3456 + i,
                'short_note': f'NOTE{i}',
                'identification_method': f'IDENT{i}',
                'museumid': f'MUSEUM{i}',
                'fieldid': f'FIELD{i}',
                'collection_code': f'COLLECT{i}',
                'processid_minted_date': f'2023-01-0{i}',
                'inst': f'INST{i}',
                'funding_src': f'FUNDING{i}',
                'sex': f'SEX{i}',
                'life_stage': f'LIFESTAGE{i}',
                'reproduction': f'REPRO{i}',
                'habitat': f'HABITAT{i}',
                'collectors': f'COLLECTORS{i}',
                'site_code': f'SITE{i}',
                'specimen_linkout': f'LINKOUT{i}',
                'collection_event_id': f'EVENT{i}',
                'sampling_protocol': f'PROTOCOL{i}',
                'tissue_type': f'TISSUE{i}',
                'collection_date_start': f'2023-02-0{i}',
                'collection_time': f'12:13:1{i}',
                'associated_taxa': f'TAXA{i}',
                'associated_specimens': f'SPECIMENS{i}',
                'voucher_type': f'VOUCHER{i}',
                'notes': f'NOTES{i}',
                'taxonomy_notes': f'TAXONOMY{i}',
                'collection_notes': f'COLLECT{i}',
                'geoid': 123 + i,
                'marker_code': f'MARKER{i}',
                'kingdom': f'KINGDOM{i}',
                'phylum': f'PHYLUM{i}',
                'class': f'CLASS{i}',
                'order': f'ORDER{i}',
                'family': f'FAMILY{i}',
                'subfamily': f'SUBFAMILY{i}',
                'tribe': f'TRIBE{i}',
                'genus': f'GENUS{i}',
                'species': f'SPECIES{i}',
                'subspecies': f'SUBSPECIES{i}',
                'taxon_name': f'TAXONNAME{i}',
                'taxon_rank': f'TAXONRANK{i}',
                'species_reference': f'SPECIESREF{i}',
                'identified_by': f'IDENTIFIEDBY{i}',
                'sequence_run_site': f'RUNSITE{i}',
                'nuc': f'NUC{i}',
                'nuc_basecount': 321 + i,
                'sequence_upload_date': f'2024-03-0{i}',
                'bin_uri': f'BINURI{i}',
                'bin_created_date': f'2024-05-0{i}',
                'elev': 14 + i,
                'depth': 15 + i,
                'coord': [
                    50.7721 + i,
                    -3.90953 + i
                ],
                'coord_source': f'COORDSOURCE{i}',
                'coord_accuracy': f'COORDACCURACY{i}',
                'elev_accuracy': f'ELEVACCURACY{i}',
                'depth_accuracy': f'DEPTHACCURACY{i}',
                'region': f'REGION{i}',
                'sector': f'SECTOR{i}',
                'site': f'SITE{i}',
                'country_iso': f'COUNTRY{i}',
                'country/ocean': f'OCEAN{i}',
                'province/state': f'STATE{i}',
                'bold_recordset_code_arr': [
                    f'RECORDSET{i}'
                ],
                'collection_date_end': f'2024-06-0{i}'
            }
            for i in range(1, 3)
        ]
        dates = [{
            'bin_created_date': datetime.datetime(2024, 5, i, 0, 0),
            'sequence_upload_date': datetime.datetime(2024, 3, i, 0, 0),
            'collection_date_start': datetime.datetime(2023, 2, i, 0, 0),
            'collection_date_end': datetime.datetime(2024, 6, i, 0, 0),
            'processid_minted_date': datetime.datetime(2023, 1, i, 0, 0)
        }
            for i in range(1, 3)
        ]
        parser = DefaultParser(_get_mock_ds_dict({'sample': {
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
        }}))
        converter = BoldApiConverter(parser)
        (out_, _) = converter.convert_list(in_)
        assert len(out_) == 2
        first = out_[0]
        assert first.type == 'sample'
        assert first.id == 'SAMPLE1'
        expected = in_[0] | dates[0]
        assert first.attributes == {k: v for k, v in expected.items() if k != 'sampleid'}
        second = out_[1]
        assert second.type == 'sample'
        assert second.id == 'SAMPLE2'
        expected = in_[1] | dates[1]
        assert second.attributes == {k: v for k, v in expected.items() if k != 'sampleid'}

    def test_convert_bin(self):
        """Test the converter for bin objects"""

        in_ = [
            {
                'phylum': {'phylum1': 10},
                'class': {'class1': 20},
                'order': {'order1': 30},
                'family': {'family1': 40},
                'genus': {'genus1': 50},
                'species': {'species1': 60}
            }
        ]
        parser = DefaultParser(_get_mock_ds_dict({'bin': {
            'kingdom': 'Dict[str, int]',
            'phylum': 'Dict[str, int]',
            'class': 'Dict[str, int]',
            'order': 'Dict[str, int]',
            'family': 'Dict[str, int]',
            'subfamily': 'Dict[str, int]',
            'tribe': 'Dict[str, int]',
            'genus': 'Dict[str, int]',
            'species': 'Dict[str, int]',
            'subspecies': 'Dict[str, int]'
        }}))
        converter = BoldApiConverter(parser)
        (out_, _) = converter.convert_list(in_)
        assert len(out_) == 1
        first = out_[0]
        assert first.type == 'bin'
        assert first.id is None
        expected = in_[0]
        assert first.attributes == expected
