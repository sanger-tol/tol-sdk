# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_treeofsex_species_to_data_object(species, target_datasource):
    for s in species:
        CoreDataObject = target_datasource.data_object_factory  # noqa N806
        ret = CoreDataObject(
            'treeofsex_species',
            attributes={
                'higher_taxanomic_group': s['Higher taxonomic group'],
                'order': s['Order'],
                'family': s['Family'],
                'genus': s['Genus'],
                'species': s['Species'],
                'species_author': s['species author'],
                'infraspecific': s['infraspecific'],
                'common_name': s['common name'],
                'hybrid': s['Hybrid'],
                'source_hybrid': s['source: Hybrid'],
                'the_plant_list_v1_1': s['ThePlantListV1.1 (1=accepted at species level,-1=recognized synonym,0=other)'],  # noqa E501
                'name_in_the_plant_list_v1_1': s['Name in ThePlantListV1.1'],
                'sexual_system': s['Sexual system'],
                'source_sexual_system': s['source: Sexual System'],
                'selfing': s['Selfing (self incompatible,self compatible)'],
                'source_selfing': s['source: Selfing'],
                'growth_form': s['Growth Form (herb,shrub,tree,herbaceous vine,liana/woody vine)'],
                'source_growth_form': s['source: Growth Form'],
                'woodiness': s['Woodiness (W, H, variable)'],
                'woodiness_count': s['Woodiness count'],
                'source_woodiness': s['source: Woodiness'],
                'life_form': s['Life Form (annual,perennial)'],
                'source_life_form': s['source: Life Form'],
                'gametophytic_chromosome_num': s['gametophytic chromosome number'],
                'gametophytic_chromosome_num_min': s['gametophytic chromosome number (minimum)'],
                'gametophytic_chromosome_num_mean': s['gametophytic chromosome number (mean)'],
                'source_gametophytic_chromosome_num': s['source: gametophytic chromosome number'],
                'sporophytic_chromosome_num': s['sporophytic chromosome number'],
                'sporophytic_chromosome_num_min': s['sporophytic chromosome number (minimum)'],
                'sporophytic_chromosome_num_mean': s['sporophytic chromosome number (mean)'],
                'source_sporophytic_chromosome_num': s['source: sporophytic chromosome number'],
                'karyotype': s['karyotype (ZO,ZW,XY,XO,WO,homomorphic,complex XY,complex ZW)'],
                'source_karyotype': s['source: karyotype'],
                'molecular_basis': s['molecular basis (dosage,Y dominant,W dominant)'],
                'source_molecular_basis': s['source: molecular basis'],
                'genotypic': s['genotypic (male heterogametic,female heterogametic,GSD,polygenic)'],  # noqa E501
                'source_genotypic': s['source: genotypic'],
                'notes': s['notes,comments'],
                'email': s['entry email'],
                'citation': s['citation']
            }
        )
        yield ret
