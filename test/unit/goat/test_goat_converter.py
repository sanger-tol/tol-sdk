# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.goat.converter import (
    GoatApiConverter
)
from tol.goat.parser import DefaultParser


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
    data_object._to_one_objects = to_one
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


class TestGoatApiConverter:
    """Tests `GoatApiConverter().convert()`"""

    def test_relationships(self):
        """A resource with relationships"""

        in_ = [
            {
                'result': {
                    'taxon_id': '9662',
                    'taxon_rank': 'species',
                    'scientific_name': 'Meles meles',
                    'fields': {
                        'genome_size': {'value': 1000},
                        'chromosome_number': {'value': 44},
                        'haploid_number': {'value': 22},
                        'assembly_level': {'value': 'Chromosome'},
                        'ploidy': {'value': 2},
                        'isb_wildlife_act_1976': {'value': 'IWA-Sch5'},
                        'protection_of_badgers_act_1992': {'value': 'Badgers92'},
                        'family_representative': {'value': 'DTOL'},
                        'sample_collected': {'value': 'DTOL'},
                        'synonym': {'value': ['Meles alba', 'Meles britannicus']}
                    },
                    'names': {
                        'tolid_prefix': {
                            'class': [
                                'tolid_prefix'
                            ],
                            'name': [
                                'mMelMel'
                            ],
                            'source': [
                                'dtol sample naming'
                            ]
                        },
                        'common_name': {
                            'class': [
                                'common_name'
                            ],
                            'name': [
                                'Melon'
                            ],
                            'source': [
                                'animal genome size database'
                            ]
                        }
                    },
                    'ranks': {
                        'species': {
                            'taxon_rank': 'species',
                            'scientific_name': 'Meles meles',
                            'taxon_id': '9662',
                            'node_depth': 0
                        },
                        'genus': {
                            'taxon_rank': 'genus',
                            'scientific_name': 'Meles',
                            'taxon_id': '9661',
                            'node_depth': 1
                        },
                        'family': {
                            'taxon_rank': 'family',
                            'scientific_name': 'Mustelidae',
                            'taxon_id': '9655',
                            'node_depth': 3
                        }
                    }
                }
            },
            {
                'result': {
                    'taxon_id': '9663',
                    'taxon_rank': 'species',
                    'scientific_name': 'Molos molos',
                    'fields': {
                        'genome_size': {'value': 2000},
                        'chromosome_number': {'value': 88},
                        'haploid_number': {'value': 44},
                        'assembly_level': {'value': 'Contig'},
                        'ploidy': {'value': 4},
                        'echabs92': {'value': 'Ech'},
                        'habreg_2017': {'value': 'Hab'},
                        'marhabreg-2017': {'value': 'Mar'},
                        'waca_1981': {'value': 'Shakira'},
                        'family_representative': {'value': ['PROJ_A', 'PROJ_B']},
                        'sample_collected': {'value': 'ZOONOMIA'},
                        'synonym': {'value': ['Molos single']}
                    }
                }
            }
        ]

        parser = DefaultParser(_get_mock_ds_dict({'taxon': {
            'scientific_name': 'str',
            'genome_size': 'int',
            'chromosome_number': 'int',
            'haploid_number': 'int',
            'assembly_level': 'str',
            'ploidy': 'int',
            'echabs92': 'str',
            'habreg_2017': 'str',
            'marhabreg-2017': 'str',
            'waca_1981': 'str',
            'isb_wildlife_act_1976': 'str',
            'family_representative': 'List[str]',
            'lineage': 'List[str]',
            'tolid_prefix': 'str',
            'common_name': 'str',
            'sample_collected': 'List[str]',
            'synonym': 'List[str]'
        }}))
        converter = GoatApiConverter(parser)
        (out_, _) = converter.convert_list(in_)
        assert len(out_) == 2
        first = out_[0]
        assert first.type == 'taxon'
        assert first.id == '9662'
        assert first.attributes == {
            'taxon_rank': 'species',
            'scientific_name': 'Meles meles',
            'genome_size': 1000,
            'chromosome_number': 44,
            'haploid_number': 22,
            'assembly_level': 'Chromosome',
            'ploidy': 2,
            'isb_wildlife_act_1976': ['IWA-Sch5'],
            'protection_of_badgers_act_1992': ['Badgers92'],
            'family_representative': ['DTOL'],
            'sample_collected': ['DTOL'],
            'lineage': ['Mustelidae', 'Meles', 'Meles meles'],
            'tolid_prefix': 'mMelMel',
            'common_name': 'Melon',
            'synonym': ['Meles alba', 'Meles britannicus']
        }
        assert first._to_one_objects['species'].id == '9662'
        assert first._to_one_objects['genus'].id == '9661'
        assert first._to_one_objects['family'].id == '9655'
        second = out_[1]
        assert second.type == 'taxon'
        assert second.id == '9663'
        assert second.attributes == {
            'taxon_rank': 'species',
            'scientific_name': 'Molos molos',
            'genome_size': 2000,
            'chromosome_number': 88,
            'haploid_number': 44,
            'assembly_level': 'Contig',
            'ploidy': 4,
            'echabs92': ['Ech'],
            'habreg_2017': ['Hab'],
            'marhabreg-2017': ['Mar'],
            'waca_1981': ['Shakira'],
            'family_representative': ['PROJ_A', 'PROJ_B'],
            'sample_collected': ['ZOONOMIA'],
            'synonym': ['Molos single']
        }
