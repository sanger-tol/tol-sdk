# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_tolid_species_to_data_object(species, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for s in species:
        ret = CoreDataObject('species', {
            'taxonomy_id': s.taxonomy_id,
            'prefix': s.prefix,
            'name': s.name,
            'common_name': s.common_name,
            'genus': s.genus,
            'family': s.family,
            'tax_order': s.tax_order,
            'tax_class': s.tax_class,
            'phylum': s.phylum,
            'kingdom': s.kingdom
        })
        yield ret
