# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import (
    DataSource,
    core_data_object
)
from ....src.tol.flows.converters import BioscanImageToElasticSampleUpdateConverter
# This import will only work once BioscanImageToElasticSampleUpdateConverter is in an sdk build
# from tol.flows.converters import BioscanImageToElasticSampleUpdateConverter
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

        # TODO: Explain this line
        CoreDataObject = source_data_source.data_object_factory
        
        # Create the data objects that will be put through the converter
        unconverted1 = CoreDataObject(
            id_='sample_one.jpeg',
            type_='object',
            attributes={
                'bucket_name': 'BUCKET_NAME_ONE',
                'last_modified': 'LAST_MODIFIED_ONE',
            }
        )
        unconverted2 = CoreDataObject(
            id_='prefix/sample_two.png',
            type_='object',
            attributes={
                'bucket_name': 'BUCKET_NAME_TWO',
                'last_modified': 'LAST_MODIFIED_TWO',
            }
        )

        # Get converted data objects
        converted1 = next(converter.convert(unconverted1))
        converted2 = next(converter.convert(unconverted2))

        # Create the data objects that we expected to have been the results of the conversions
        expected1 = (None, {
            'sts_specimen.id': 'sample_one',
            'bioscan_image_url': 'https://BUCKET_NAME_ONE.cog.sanger.ac.uk/sample_one.jpeg',
            'bioscan_image_modified': 'LAST_MODIFIED_ONE',
        })
        expected2 = (None, {
            'sts_specimen.id': 'sample_two',
            'bioscan-image_url': 'https://BUCKET_NAME_TWO.cog.sanger.ac.uk/prefix/sample_two.png',
            'bioscan_image_modified': 'LAST_MODIFIED_TWO',
        })

        # Check whether the converted data objects are the same as we expected
        self.assertEqual(converted1, expected1)
        self.assertEqual(converted2, expected2)
