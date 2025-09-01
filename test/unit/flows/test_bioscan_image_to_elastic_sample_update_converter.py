# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from unittest import TestCase

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import BioscanImageToElasticSampleUpdateConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['object', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioscanImageToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):
        # The data source that we're flowing from
        source_data_source = _MockDataSource(config={})
        core_data_object(source_data_source)

        # The data source that we're flowing to
        destination_data_source = _MockDataSource(config={})
        core_data_object(destination_data_source)

        # Initialize converter
        converter = BioscanImageToElasticSampleUpdateConverter(
            data_object_factory=destination_data_source.data_object_factory
        )

        # Make a "mock class" that's actually the data_object_factory of the source data source
        # to allow data objects to be created from this data source (to go into the converter)
        # noqa N806 tells the linter to ignore that CoreDataObject should be in lowercase
        CoreDataObject = source_data_source.data_object_factory  # noqa N806

        # Create the data objects that will be put through the converter
        unconverted1 = CoreDataObject(
            id_='sample_one.jpeg',
            type_='object',
            attributes={
                'bucket_name': 'BUCKET_NAME_ONE',
                'last_modified': datetime(2020, 1, 1),
            }
        )
        unconverted2 = CoreDataObject(
            id_='prefix/sample_two.png',
            type_='object',
            attributes={
                'bucket_name': 'BUCKET_NAME_TWO',
                'last_modified': datetime(2023, 5, 7),
            }
        )

        # Get converted data objects
        converted1 = next(converter.convert(unconverted1))
        converted2 = next(converter.convert(unconverted2))

        # Create the data objects that we expected to have been the results of the conversions
        expected1 = (None, {
            'sts_specimen.id': 'sample_one',
            'bioscan_image_url': 'https://BUCKET_NAME_ONE.cog.sanger.ac.uk/sample_one.jpeg',
            'bioscan_image_modified': datetime(2020, 1, 1),
        })
        expected2 = (None, {
            'sts_specimen.id': 'sample_two',
            'bioscan_image_url': 'https://BUCKET_NAME_TWO.cog.sanger.ac.uk/prefix/sample_two.png',
            'bioscan_image_modified': datetime(2023, 5, 7),
        })

        # Check whether the converted data objects are the same as we expected
        self.assertEqual(converted1, expected1)
        self.assertEqual(converted2, expected2)
