# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.sources.gap import gap


class TestGapDataSource(TestCase):

    def test_attribute_types(self):
        gds = gap()
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
        gsds = gap()

        ret = gsds.get_by_id('assembly', ['GCA_002706865.2'])
        obj1 = next(ret)
        self.assertEqual('GCA_002706865.2', obj1.id)
        self.assertEqual({
            'project': None,
            'phylum': 'Arthropoda',
            'species': 'Spodoptera litura',
            'assembly_name': 'ASM270686v2',
            'results': (
                "<a href='https://gap.cog.sanger.ac.uk/browser.html?shared=GCA_002706865.2/"
                "Spodoptera_litura/analysis/GCA_002706865.2/base_content/'>Base Content</a><br>"
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
                '/lustre/scratch122/tol/data/4/1/3/3/e/1/Spodoptera_litura/'
                'analysis/GCA_002706865.2'
            ),
            'lustre_path_assembly': (
                '/lustre/scratch122/tol/data/4/1/3/3/e/1/Spodoptera_litura/assembly/'
                'release/GCA_002706865.2/insdc'
            ),
            'lustre_path_species': (
                '/lustre/scratch122/tol/data/4/1/3/3/e/1/Spodoptera_litura'
            )
        }, obj1.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_to_many_relations(self):
        gsds = gap()

        assembly = gsds.get_by_id('assembly', ['GCA_002706865.2'])
        pipelines = next(assembly).pipelines
        pipeline1 = next(pipelines)
        self.assertEqual({
            'analysis': 'Sequence Composition',
            'results': 'Base Content',
            'description': (
                "\u003Ca href='https://pipelines.tol.sanger.ac.uk/sequencecomposition/"
                "output#sequence-composition-files'\u003ESequence composition "
                "k-mer files\u003C/a\u003E" # noqa
            ),
            's3': (
                'https://gap.cog.sanger.ac.uk/browser.html?shared=GCA_002706865.2/'
                'Spodoptera_litura/analysis/GCA_002706865.2/base_content/'
            ),
            'lustre_path_analysis': (
                '/lustre/scratch122/tol/data/4/1/3/3/e/1/Spodoptera_litura/analysis/'
                'GCA_002706865.2/base_content'
            )
        }, pipeline1.attributes)

        pipeline2 = next(pipelines)
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
        }, pipeline2.attributes)

        with self.assertRaises(StopIteration):
            next(assembly)
