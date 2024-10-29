# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.ena.converter import (
    EnaApiConverter
)
from tol.ena.parser import DefaultParser


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    return data_object


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {},
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


class TestEnaApiConverter:
    """Tests `EnaApiConverter`.convert()."""

    def test_convert(self):
        """Test convert()."""

        in_ = [
            {
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Archelosauria; Archosauria; Dinosauria; Saurischia; Theropoda; Coelurosauria; Aves; Neognathae; Neoaves; Aequornithes; Suliformes; Phalacrocoracidae; Phalacrocorax; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '',
                'description': 'Phalacrocorax aristotelis',
                'accession': '126867',
                'synonym': 'Gulosus aristotelis (Linnaeus;1761):authority;Pelecanus aristotelis Linnaeus;1761:authority;Phalacrocorax aristotelis (Linnaeus;1761):authority;European shag:common name;Pelecanus aristotelis:synonym;Gulosus aristotelis:synonym;Leucocarbo aristotelis:synonym;Phalacrocorax aristotelis:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;8457;32561;1329799;8492;436486;436489;436491;436492;8782;8825;3078114;3073812;3073854;9206;9207;126867', # noqa
                'rank': 'species',
                'tag': 'env_tax:terrestrial;env_tax:marine;xref:WoRMS',
                'common_name': 'European shag',
                'tax_division': 'VRT',
                'genbank_common_name': '',
                'status': 'public'
            },
            {
                'tax_id': '10090',
                'scientific_name': 'Mus musculus',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia; Eutheria; Euarchontoglires; Glires; Rodentia; Myomorpha; Muroidea; Muridae; Murinae; Mus; Mus; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '85055',
                'description': 'Mus musculus',
                'accession': '10090',
                'synonym': 'mice C57BL/6xCBA/CaJ hybrid:misspelling;Mus musculus Linnaeus;1758:authority;LK3 transgenic mice:includes;transgenic mice:includes;Mus sp. 129SV:includes;nude mice:includes;mouse:common name;mouse <Mus musculus>:common name;house mouse:genbank common name;Mus musculus:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;40674;32525;9347;1437010;314146;314147;9989;1963758;337687;10066;39107;10088;862507;10090', # noqa
                'rank': 'species',
                'tag': '',
                'common_name': 'mouse',
                'tax_division': 'MUS',
                'genbank_common_name': 'house mouse',
                'status': 'public'
            }
        ]
        parser = DefaultParser(
            _get_mock_ds_dict({'taxon': {
                'tax_id': {'type': 'string'},
                'scientific_name': {'type': 'string'},
                'lineage': {'type': 'string'},
                'genetic_code': {'type': 'string'},
                'merged_tax_id': {'type': 'string'},
                'description': {'type': 'string'},
                'accession': {'type': 'string'},
                'synonym': {'type': 'string'},
                'tax_lineage': {'type': 'string'},
                'rank': {'type': 'string'},
                'tag': {'type': 'string'},
                'common_name': {'type': 'string'},
                'tax_division': {'type': 'string'},
                'genbank_common_name': {'type': 'string'},
                'status': {'type': 'string'}
            }})
        )

        converter = EnaApiConverter(parser)
        (out_, _) = converter.convert_list('taxon', in_)
        assert len(out_) == 2
        first = out_[0]
        assert first.type == 'taxon'
        assert first.id == '126867'
        second = out_[1]
        assert second.type == 'taxon'
        assert second.id == '10090'
