# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest import TestCase

from tol.core import core_data_object
from tol.gap import GapDataSource


def gap_data_source() -> GapDataSource:
    gds = GapDataSource({
        'uri': 's3://gap/data/assembly.json',
        'type': 'assembly',
        'id_attribute': 'accession',
        's3_host': 'cog.sanger.ac.uk',
        's3_access_key': os.getenv('MINIO_ACCESS_KEY'),
        's3_secret_key': os.getenv('MINIO_SECRET_KEY'),
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
    cdo = core_data_object(gds)
    return cdo, gds


class TestGapDataSource(TestCase):

    def test_attribute_types(self):
        _, gds = gap_data_source()
        expected = {
            'assembly': {
                'project': 'str',
                'phylum': 'str',
                'species': 'str',
                'accession': 'str',
                'assembly_name': 'str',
                'results': 'str',
                'taxon_id': 'int',
                'phylum_id': 'str',
                'image_url': 'str',
                'image_caption': 'str',
                'lustre_path_analysis_base': 'str',
                'lustre_path_assembly': 'str',
                'lustre_path_species': 'str',
            }
        }
        self.assertEqual(expected, gds.attribute_types)
        self.assertEqual(['assembly'], gds.supported_types)

    def test_get_by_id(self):
        _, gsds = gap_data_source()

        ret = gsds.get_by_id('assembly', ['GCA_002706865.2'])
        obj1 = next(ret)
        self.assertEqual('GCA_002706865.2', obj1.id)
        self.assertEqual({
            'project': 'Lepidoptera',
            'phylum': 'Arthropoda',
            'species': 'Spodoptera litura',
            'assembly_name': 'ASM270686v2',
            'results': (
                "<a href='https://gap.cog.sanger.ac.uk/browser.html?"
                "shared=GCA_002706865.2/base_content/'>Base Content</a><br>"
                "<a href='https://blobtoolkit.genomehubs.org/view/dataset/"
                "GCA_002706865.1/dataset/MTZO01.1/blob#Filters'>BlobToolKit</a>"
            ),
            'taxon_id': 69820,
            'phylum_id': '6656',
            'image_url': (
                'https://inaturalist-open-data.s3.amazonaws.com/photos/253028015/medium.jpg'
            ),
            'image_caption': '<i>Spodoptera litura</i><br> (Phylum Arthropoda)',
            'lustre_path_analysis_base': (
                '/lustre/scratch123/tol/projects/lepidoptera/data/insects/'
                'Spodoptera_litura/analysis/ASM270686v2'
            ),
            'lustre_path_assembly': (
                '/lustre/scratch123/tol/projects/lepidoptera/data/insects/'
                'Spodoptera_litura/assembly/release/ASM270686v2/insdc'
            ),
            'lustre_path_species': (
                '/lustre/scratch123/tol/projects/lepidoptera/data/insects/Spodoptera_litura'
            )
        }, obj1.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_to_many_relations(self):
        _, gsds = gap_data_source()

        assembly = gsds.get_by_id('assembly', ['GCA_002706865.2'])
        ret = gsds.get_to_many_relations(next(assembly))
        obj1 = next(ret)
        self.assertEqual({
            'analysis': 'Sequence Composition',
            'results': 'Base Content',
            'description': (
                "\u003Ca href='https://pipelines.tol.sanger.ac.uk/sequencecomposition/"
                "output#sequence-composition-files'\u003ESequence composition "
                "k-mer files\u003C/a\u003E" # noqa
            ),
            's3': (
                'https://gap.cog.sanger.ac.uk/browser.html?shared=GCA_002706865.2/base_content/'
            ),
            'lustre_path_analysis': (
                '/lustre/scratch123/tol/projects/lepidoptera/data/insects/Spodoptera_litura/'
                'analysis/ASM270686v2/base_content'
            )
        }, obj1.attributes)

        obj2 = next(ret)
        self.assertEqual({
            'analysis': 'BlobToolKit',
            'results': 'BlobToolKit',
            'description': (
                'The BlobToolKit Viewer allows interactive exploration of '
                "<a href='https://blobtoolkit.genomehubs.org/specification/'>BlobDir</a> "
                'datasets produced by <a href='
                "'https://blobtoolkit.genomehubs.org/blobtools2/'>BlobTools2</a> "
                'to aid in the identification and filtering of contaminants and '
                'other cobionts as part of the assembly QC process.'
            ),
            's3': (
                'https://blobtoolkit.genomehubs.org/view/dataset/GCA_002706865.1/'
                'dataset/MTZO01.1/blob#Filters'
            ),
            'lustre_path_analysis': None
        }, obj2.attributes)

        with self.assertRaises(StopIteration):
            next(ret)
