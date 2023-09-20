# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_bold_samples_to_data_object(samples, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    mapping = {
        'phylum': 'taxonomy_phylum_taxon_name',
        'class': 'taxonomy_class_taxon_name',
        'order': 'taxonomy_order_taxon_name',
        'family': 'taxonomy_family_taxon_name',
        'subfamily': 'taxonomy_subfamily_taxon_name',
        'genus': 'taxonomy_genus_taxon_name',
        'specimen_id': 'specimen_identifiers_sampleid',
        'collector_sample_id': 'specimen_identifiers_catalognum',
        'institution_storing': 'specimen_identifiers_institution_storing',
        'voucher_status': 'specimen_desc_voucher_status',
        'lifestage': 'specimen_desc_lifestage',
        'organism_part': 'specimen_desc_organism_part',
        'gal': 'collection_event_collectors',
        'collection_country': 'collection_event_country',
        'exact_site': 'collection_event_exactsite',
        'decimal_latitude': 'collection_event_coordinates_lat',
        'decimal_longitude': 'collection_event_coordinates_long',
        'site_code': 'collection_event_site_code',
        'collection_method': 'collection_event_site_sampling_protocol'
    }
    for s in samples:
        attributes = {k: getattr(s, v)
                      for k, v in mapping.items()
                      if v in s.attributes}
        ret = CoreDataObject('sample', attributes)
        yield ret
