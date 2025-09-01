# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, Tuple

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


def extract_data_from_s3_url(s3_url: str) -> Tuple[str, str, str]:
    """
    Extracts the file name, bucket name, and sample id of a Bioscan image
    from its S3 path, which is assumed to be in the format

    'S3://`<bucket name>`/`<prefix>`/`<sample id>`.`<suffix>`'

    :returns: bucket_name, file_name, sample_id
    """
    split_url = s3_url.split('/')

    # TODO: Do this better with regular expressions
    bucket_name = split_url[2]
    file_name = split_url[-1]
    sample_id = file_name.split('.')[0]

    return bucket_name, file_name, sample_id


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

        # The id of an S3 bucket data object is its S3 URL
        # This URL contains the bucket name, as well as the sample id
        # (within the file name at the end)
        # The following function extracts these.
        # TODO: Can't you just get `bucket_name` from `input_` itself?
        bucket_name, file_name, sample_id = extract_data_from_s3_url(input_.id)

        # Construct the URL for the Bioscan image using this information
        bioscan_image_url = f'https://{bucket_name}.cog.sanger.ac.uk/{file_name}'

        attributes = {
            # For a Bioscan image, the specimen id and sample id are the same,
            # because a Bioscan sample is the whole specimen (an entire insect)
            'sts_specimen.id': sample_id,
            'bioscan_image_url': bioscan_image_url,
            'bioscan_image_modified': input_.last_modifed
        }

        yield (None, attributes)  # type: ignore (Linter does not properly recognise type here)
