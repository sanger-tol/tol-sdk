# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    GritIssueToElasticCurationConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['issue', 'user']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_issue = RelationshipConfig()
        rc_issue.to_one = {
            'reporter': 'user',
            'assignee': 'user'
        }
        return {
            'issue': rc_issue
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSourceRelational2(DataSource, Relational):

    @property
    def supported_types(self):
        return ['curation', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_curation = RelationshipConfig()
        rc_curation.to_one = {
            'tolid': 'tolid'
        }
        return {
            'curation': rc_curation
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestGritIssueToElasticCurationConverter:
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceRelational2(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GritIssueToElasticCurationConverter(
            data_object_factory=destination.data_object_factory,
            config=GritIssueToElasticCurationConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        user = CoreDataObject(
            id_='test_user',
            type_='user',
            attributes={
                'email': 'test@test.com',
                'name': 'test',
                'displayName': 'Test User'
            }
        )
        issue = CoreDataObject(
            id_='KEY-123',
            type_='issue',
            attributes={
                'created': datetime(2020, 2, 2),
                'sample_id': 'abCdeFghi1-something',
                'tolid': 'abCdeFghi1',
                'description': 'Ignore',
                'assembled_by': 'ToL',
                'status_changes': [
                    {
                        'this_status': 'Open',
                        'next_status': 'Mid Range',
                        'start_date': datetime(2020, 2, 2),
                        'end_date': datetime(2020, 2, 3)
                    }, {
                        'this_status': 'Open',
                        'next_status': 'Closed',
                        'start_date': datetime(2020, 2, 3),
                        'end_date': datetime(2020, 2, 4)
                    }
                ],
                'labels': ['BLAX', 'combine_for_curation', 'manual_submission'],
                'assembly_statistics': 'scaffolds\ntotal 333046658 333047658\ncount 41 36\nN50 11581856 11581856\nL50 3 4    \nN90 7014107 7711609\nL90 27 27\n\ncontigs\ntotal 333046218 333046218\ncount 44 44\nN50 11581856 11581856\nL50 13 13\nN90 7014107 7014107\nL90 27 27\n',  # noqa E501
                'chromosome_result': 'found 31 autosomes and W and Z and MT\nTotal length 333047658\nChr length 332949469\nChr length 99.97 %\n',  # noqa E501
                'treeval': 'hap1: ilLysCori39_1 hap2: ilLysCori39_2 merged: ilLysCori39_3',
                'treeval_data': '{"jbrowse": "ilLysCori39_1", "jb_server": "prod", "jb_scaffold": "SCAFFOLD_1", "start": "2023-11-22T12:57:44.000+0000", "btk_pr": "ilLysCori39.20231118", "btk_hp": "ilLysCori39.20231118.haplotigs", "higlass": "", "hic_plot": "Y", "kmer_plot": "N", "taxon_id": 268709}',  # noqa E501
                'contamination': 'Total length of scaffolds removed: 143,860 (0.0 %) Scaffolds removed: 6 (4.2 %) Largest scaffold removed: (39,584) FCS-GX contaminant species (number of scaffolds; total length of scaffolds): Sodalis glossinidius, g-proteobacteria (1; 39,584) Candidatus Symbiopectobacterium sp. Clec_Harlan, g-proteobacteria (1; 34,354) Mitochondrion (4; 69,905) Barcodes (1; 17) ',  # noqa E501
            },
            to_one={
                'reporter': user,
                'assignee': user
            }
        )
        converteds = converter.convert(issue)
        ret1 = next(converteds)
        assert ret1.id == 'KEY-123'
        assert ret1.type == 'curation'
        assert ret1.attributes == {
            'assembled_by': 'ToL',
            'labels': ['BLAX', 'combine_for_curation', 'manual_submission'],
            'created': datetime(2020, 2, 2),
            'mid_range_date': datetime(2020, 2, 3),
            'closed_date': datetime(2020, 2, 4),
            'scaffolds_total_before': 333046658,
            'scaffolds_total_after': 333047658,
            'scaffolds_total_change_per': 0.0003002582298844146,
            'scaffolds_count_before': 41,
            'scaffolds_count_after': 36,
            'scaffolds_count_change_per': -12.195121951219512,
            'scaffolds_n50_before': 11581856,
            'scaffolds_n50_after': 11581856,
            'scaffolds_n50_change_per': 0.0,
            'scaffolds_l50_before': 3,
            'scaffolds_l50_after': 4,
            'scaffolds_l50_change_per': 33.33333333333333,
            'scaffolds_n90_before': 7014107,
            'scaffolds_n90_after': 7711609,
            'scaffolds_n90_change_per': 9.944273732921383,
            'scaffolds_l90_before': 27,
            'scaffolds_l90_after': 27,
            'scaffolds_l90_change_per': 0.0,
            'contigs_total_before': 333046218,
            'contigs_total_after': 333046218,
            'contigs_total_change_per': 0.0,
            'contigs_count_before': 44,
            'contigs_count_after': 44,
            'contigs_count_change_per': 0.0,
            'contigs_n50_before': 11581856,
            'contigs_n50_after': 11581856,
            'contigs_n50_change_per': 0.0,
            'contigs_l50_before': 13,
            'contigs_l50_after': 13,
            'contigs_l50_change_per': 0.0,
            'contigs_n90_before': 7014107,
            'contigs_n90_after': 7014107,
            'contigs_n90_change_per': 0.0,
            'contigs_l90_before': 27,
            'contigs_l90_after': 27,
            'contigs_l90_change_per': 0.0,
            'chr_ass': 'found 31 autosomes',
            'ass_percent': '99.97',
            'assignee_name': 'test',
            'sample_id': 'abCdeFghi1-something',
            'treeval_jbrowse': 'ilLysCori39_1',
            'treeval_jb_server': 'prod',
            'treeval_jb_scaffold': 'SCAFFOLD_1',
            'treeval_start': '2023-11-22T12:57:44.000+0000',
            'treeval_btk_pr': 'ilLysCori39.20231118',
            'treeval_btk_hp': 'ilLysCori39.20231118.haplotigs',
            'treeval_higlass': '',
            'treeval_hic_plot': 'Y',
            'treeval_kmer_plot': 'N',
            'treeval_taxon_id': 268709,
            'treeval_hap1_analysis': 'ilLysCori39_1',
            'treeval_hap2_analysis': 'ilLysCori39_2',
            'treeval_merged_analysis': 'ilLysCori39_3',
            'contamination_total_removed': 143_860.0,
            'contamination_total_removed_percent': 0.0,
            'contamination_count_removed': 6.0,
            'contamination_count_removed_percent': 4.2,
            'contamination_largest_removed': 39_584.0,
            'contamination_is_abnormal': False,
            'treeval': 'hap1: ilLysCori39_1 hap2: ilLysCori39_2 merged: ilLysCori39_3',
            'treeval_data': '{"jbrowse": "ilLysCori39_1", "jb_server": "prod", "jb_scaffold": "SCAFFOLD_1", "start": "2023-11-22T12:57:44.000+0000", "btk_pr": "ilLysCori39.20231118", "btk_hp": "ilLysCori39.20231118.haplotigs", "higlass": "", "hic_plot": "Y", "kmer_plot": "N", "taxon_id": 268709}',  # noqa E501
            'treeval_hic_map_link': 'https://treeval.cog.sanger.ac.uk/pretextsnapshot_ilLysCori39_3.png',  # noqa E501
            'treeval_kmer_spectra_link': 'https://treeval.cog.sanger.ac.uk/kmerspectra_ilLysCori39_3.png',  # noqa E501
            'treeval_jbrowse_link': r'http://jbrowse.tol.sanger.ac.uk/jbrowse2/?config=config.json&assembly=ilLysCori39_1&session=spec-{%22views%22:[{%22assembly%22:%22ilLysCori39_1%22,%22loc%22:%22SCAFFOLD_1%22,%22type%22:%22LinearGenomeView%22,%22tracks%22:[%22ilLysCori39_1-ReferenceSequenceTrack%22]}]}',  # noqa E501
            'contamination': 'Total length of scaffolds removed: 143,860 (0.0 %) Scaffolds removed: 6 (4.2 %) Largest scaffold removed: (39,584) FCS-GX contaminant species (number of scaffolds; total length of scaffolds): Sodalis glossinidius, g-proteobacteria (1; 39,584) Candidatus Symbiopectobacterium sp. Clec_Harlan, g-proteobacteria (1; 34,354) Mitochondrion (4; 69,905) Barcodes (1; 17) ',  # noqa E501
        }
        assert ret1.tolid.id == 'abCdeFghi1'

        with pytest.raises(StopIteration):
            next(converteds)

        issue.assembled_by = 'Someone Else'
        converteds = converter.convert(issue)
        with pytest.raises(StopIteration):
            next(converteds)
