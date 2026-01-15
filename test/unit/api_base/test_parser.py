# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta, timezone

import pytest

from tol.api_client.parser import DefaultParser
from tol.api_client.view import DefaultView
from tol.core import DataSourceDict, ReqFieldsTree


@pytest.fixture
def mock_rel_ds_dict(mock_rel_ds):
    return DataSourceDict(mock_rel_ds)


@pytest.fixture
def tz1():
    return timezone(timedelta(hours=1))


class TestDefaultParser:
    def test_no_attributes(self, mock_rel_ds_dict):
        """
        Parse with no attributes (or relationships), just type and ID.
        """

        (parsed,) = DefaultParser(mock_rel_ds_dict).parse_json_doc(
            {
                'data': {
                    'type': 'sample_typ',
                    'id': 'SMPL009',
                }
            }
        )

        assert parsed.type == 'sample_typ'
        assert parsed.id == 'SMPL009'
        assert not parsed.attributes
        assert not parsed._to_one_objects
        assert not parsed._to_many_objects

    def test_no_relationships(self, mock_rel_ds_dict, tz1):
        """
        Parse with no relationships, but with type and ID, and tests parsing
        of all attribute types.
        """

        (parsed,) = DefaultParser(mock_rel_ds_dict).parse_json_doc(
            {
                'data': {
                    'type': 'dna_typ',
                    'id': 'DNA009',
                    'attributes': {
                        'date': '1998-05-30T11:30:07+01:00',
                        'bases': 3_000_000,
                        'reads': 42,
                        'mean_read_length': 71428.571,
                    },
                }
            }
        )

        assert parsed.type == 'dna_typ'
        assert parsed.id == 'DNA009'
        assert parsed.attributes == {
            'date': datetime(1998, 5, 30, 11, 30, 7, tzinfo=tz1),
            'bases': 3_000_000,
            'reads': 42,
            'mean_read_length': 71428.571,
        }

    def test_parse_iterable(self, mock_rel_ds_dict):
        """
        Parsing a list of three objects. Objects can only be of one type.
        """

        parsed = DefaultParser(mock_rel_ds_dict).parse_json_doc(
            {
                'data': [
                    {
                        'type': 'sample_typ',
                        'id': f'SMPL#00{i}',
                        'attributes': {
                            'lims_id': f'LIMS#00{i}',
                        },
                    }
                    for i in range(2, 5)
                ]
            }
        )

        assert len(parsed) == 3
        assert all(x.type == 'sample_typ' for x in parsed)
        assert [x.id for x in parsed] == [
            'SMPL#002',
            'SMPL#003',
            'SMPL#004',
        ]
        assert [x.lims_id for x in parsed] == [
            'LIMS#002',
            'LIMS#003',
            'LIMS#004',
        ]

    def test_full_resource(self, mock_rel_ds, mock_rel_ds_dict):
        """
        Test parsing related to-one and to-many objects from `included`
        array.
        """

        json_doc = {
            'data': [
                {
                    'type': 'sample_typ',
                    'id': 'SMPL#009',
                    'attributes': {
                        'lims_id': 'JurasicPark#009',
                    },
                    'relationships': {
                        'specimen_rel': {
                            'data': {
                                'type': 'specimen_typ',
                                'id': 'rTyrRex1',
                            }
                        },
                        'dna_rel': {
                            'data': [
                                {
                                    'type': 'dna_typ',
                                    'id': 'DNA011',
                                },
                                {
                                    'type': 'dna_typ',
                                    'id': 'DNA012',
                                },
                            ],
                        },
                    },
                },
                {
                    'type': 'sample_typ',
                    'id': 'SMPL#040',
                    'attributes': {
                        'lims_id': 'JurasicPark#040',
                    },
                    'relationships': {
                        'specimen_rel': {
                            'data': {
                                'type': 'specimen_typ',
                                'id': 'rTyrRex1',
                            }
                        },
                        'dna_rel': {
                            'data': [
                                {
                                    'type': 'dna_typ',
                                    'id': 'DNA043',
                                }
                            ],
                        },
                    },
                },
            ],
            'included': [
                {
                    'type': 'species_typ',
                    'id': 'Tyranosaurus rex',
                    'attributes': {
                        'common_name': 'king tyrant lizard',
                    },
                    'relationships': {
                        'specimen_list': {
                            'links': {
                                'related': '/data/species_typ/Tyranosaurus%20rex/specimen_list'
                            }
                        }
                    },
                },
                {
                    'type': 'specimen_typ',
                    'id': 'rTyrRex1',
                    'attributes': {
                        'collected_on': '1993-02-28T19:45:00',
                    },
                    'relationships': {
                        'species_rel': {
                            'data': {
                                'type': 'species_typ',
                                'id': 'Tyranosaurus rex',
                            }
                        },
                        'sample_list': {
                            'links': {
                                'related': '/data/specimen_typ/rTyrRex1/sample_list'
                            }
                        },
                    },
                },
                {
                    'type': 'dna_typ',
                    'id': 'DNA011',
                    'attributes': {
                        'bases': 1_300_456,
                        'date': '1993-06-09T12:30:00',
                    },
                },
                {
                    'type': 'dna_typ',
                    'id': 'DNA012',
                    'attributes': {
                        'bases': 3_400_729,
                        'date': '1993-06-15T14:30:59',
                    },
                },
                {
                    'type': 'dna_typ',
                    'id': 'DNA043',
                    'attributes': {
                        'reads': 6632,
                    },
                },
            ],
        }

        req_tree = ReqFieldsTree(
            'sample_typ',
            mock_rel_ds,
            requested_fields=[
                'specimen_rel.species_rel',
                'dna_rel',
            ],
        )

        parsed = DefaultParser(mock_rel_ds_dict, req_tree).parse_json_doc(json_doc)
        smpl09, smpl40 = parsed
        assert smpl09.id == 'SMPL#009'
        assert smpl40.id == 'SMPL#040'
        assert smpl09.specimen_rel.id == 'rTyrRex1'
        assert smpl09.specimen_rel.collected_on == datetime(  # noqa: DTZ001
            1993, 2, 28, 19, 45
        )

        # Relationships for both samples are linked to the same specimen and
        # species `DataObject`
        assert smpl09.specimen_rel is smpl40.specimen_rel
        assert smpl09.specimen_rel.species_rel is smpl40.specimen_rel.species_rel
        # `species_typ` object is not a stub
        assert smpl09.specimen_rel.species_rel.common_name == 'king tyrant lizard'

        # Expected number of to-many objects are present and are not stubs
        dna09 = smpl09.dna_rel
        assert len(dna09) == 2
        assert dna09[0].id == 'DNA011'
        assert dna09[1].id == 'DNA012'
        assert dna09[0].bases == 1_300_456
        assert dna09[1].bases == 3_400_729

        dna40 = smpl40.dna_rel
        assert len(dna40) == 1
        assert dna40[0].id == 'DNA043'
        assert dna40[0].reads == 6632

        # Test round trip of parsed data back to JSON doc
        view = DefaultView(req_tree, prefix='/data')
        dumped_json = view.dump_bulk(parsed)
        assert json_doc == dumped_json
