# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from ..core import (
    core_data_object
)
from ..gap import (
    GapDataSource
)


def gap(**kwargs) -> GapDataSource:
    gap = GapDataSource({
        'uri': 's3://gap/data/assembly.json',
        'type': 'assembly',
        'id_attribute': 'accession',
        's3_host': 'cog.sanger.ac.uk',
        's3_access_key': None,
        's3_secret_key': None,
        'mappings': {
            'project': {'heading': 'project', 'type': 'str'},
            'phylum': {'heading': 'phylum', 'type': 'str'},
            'species': {'heading': 'species', 'type': 'str'},
            'accession': {'heading': 'accession', 'type': 'str'},
            'assembly_name': {'heading': 'assembly_name', 'type': 'str'},
            'results': {'heading': 'results', 'type': 'str'},
            'taxon_id': {'heading': 'taxon_id', 'type': 'int'},
            'phylum_id': {'heading': 'phylum_id', 'type': 'str'},
            'image_url': {'heading': 'image_url', 'type': 'str'},
            'image_caption': {'heading': 'image_caption', 'type': 'str'},
            'lustre_path_analysis_base': {
                'heading': 'lustre_path_analysis_base', 'type': 'str'
            },
            'lustre_path_assembly': {
                'heading': 'lustre_path_assembly', 'type': 'str'
            },
            'lustre_path_species': {
                'heading': 'lustre_path_species', 'type': 'str'
            }
        }
    })
    core_data_object(gap)
    return gap
