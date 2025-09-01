# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BioscanImageToElasticSampleUpdateConverter(
    DataObjectToDataObjectOrUpdateConverter
):
    """
    Converter for Bioscan images stored in S3 Buckets
    into an Updater Data Object for Elastic (Portal's data source)
    """
    def convert(self, input_: DataObject) -> Iterable[DataObjectUpdate]:
        """
        Converts a Data Object of type 'object' representing a Bioscan image
        stored in an S3 bucket into an Updater Data Object for Elastic (Portal's data source)

        :param input_: The input data object from an S3 bucket storing a Bioscan image.
        Has type 'object' and must have an id (its file name on S3)

        :returns: A generator of output `DataObjectUpdate`s which can be used to update
        the the sample data objects in Elastic
        """
        # Ensure a data object has been passed in
        if input_ is None:
            return

        # Ensure the data object has an id
        if input_.id is None:
            return

        # Get S3 bucket name from input Bioscan image data object
        bucket_name = input_.attributes['bucket_name']

        # The id of a Bioscan image is its S3 file name
        bioscan_image_file_name = input_.id

        # This file name contains the sample id of the Bioscan image
        # The following function extracts this
        sample_id = self.__extract_sample_id_from_s3_file_name(bioscan_image_file_name)

        # Construct the URL for the Bioscan image using this information
        bioscan_image_url = f'https://{bucket_name}.cog.sanger.ac.uk/{bioscan_image_file_name}'

        attributes = {
            # For a Bioscan image, the specimen id and sample id are the same,
            # because a Bioscan sample is the whole specimen (an entire insect)
            'sts_specimen.id': sample_id,
            'bioscan_image_url': bioscan_image_url,
            'bioscan_image_modified': input_.attributes['last_modified']
        }

        yield (None, attributes)  # type: ignore (Linter does not properly recognise type here)

    def __extract_sample_id_from_s3_file_name(self, file_name: str) -> str:
        """
        Extracts the sample id of a Bioscan image from its S3 file name,
        which is assumed to be in the format

        '`<prefix>`/`<sample id>`.`<suffix>`',
        where `<prefix>/` is optional

        :returns: sample_id
        """
        # Remove file prefix (even if not present)
        file_name_without_prefix = file_name.split('/')[-1]

        # Remove file suffix
        sample_id = file_name_without_prefix.split('.')[0]

        return sample_id
