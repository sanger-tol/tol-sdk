# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from functools import cache
import json
from io import BytesIO
from minio import Minio

from typing import Any, Dict, Iterable, Optional

from dateutil import parser as dateutil_parser

from . import JsonDataSource

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import (
    ListGetter,
)


class S3JsonDataSource(
    DataSource,
    ListGetter
):
    """
    A subclass of JsonDataSource that loads JSON data directly from an S3 bucket.
    """

    def __init__(
        self,
        config: dict,
        s3_endpoint: str,
        s3_access_key: str,
        s3_secret_key: str,
        s3_bucket: str,
        s3_object: str,
        secure: bool = True
    ) -> None:
        DataSource.__init__(self, config=config)
        
        # Initialize MinIO client
        self.minio_client = Minio(
            s3_endpoint,
            access_key=s3_access_key,
            secret_key=s3_secret_key,
            secure=secure
        )
        
        self.config = config
        self.id_attribute = config.get("id_attribute")

        # Load JSON data from S3
        raw_data = self._load_json_from_s3(s3_bucket, s3_object)

        # Set raw data
        self.__raw_data = raw_data
        self.__keyed_by_id = {
            v[self.id_attribute]: v
            for v in self.__raw_data
            if self.id_attribute in v
        }
    
    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            self.type: {
                k: v['type']
                for k, v in self.mappings.items()
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )
        
    def _load_json_from_s3(self, bucket: str, object_name: str):
        """Fetch and load JSON data from an S3 bucket."""
        try:
            response = self.minio_client.get_object(bucket, object_name)
            json_data = json.load(BytesIO(response.read()))  # Read and parse JSON
            return json_data
        except Exception as e:
            raise DataSourceError(f"Failed to load JSON from S3: {e}")
        
    def __map_entry(self, entry: Dict):
        ret = {}
        for mapping_key, mapping_value in self.mappings.items():
            if mapping_value['heading'] != self.id_attribute:
                subentry = entry
                for level in mapping_value['heading'].split('.'):
                    if subentry is not None:
                        subentry = subentry.get(level)
                ret[mapping_key] = self.__parse_date(mapping_key, subentry)
        return ret

    def __parse_date(self, attribute_name: str, value: Any):
        if self.mappings[attribute_name]['type'] == 'datetime' and value is not None:
            return dateutil_parser.parse(value)
        if self.mappings[attribute_name]['type'] == 'str' and value is not None:
            return str(value)
        return value
        
    def __create_data_object(self, entry: Dict):
        return self.data_object_factory(
            self.type,
            entry.get(self.id_attribute),
            attributes=self.__map_entry(entry)
        )
        
    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None
    ) -> Iterable[DataObject]:
        """
        Gets an Iterable of DataObject instances of the given
        type, according to the given DataSourceFilter.
        """
        if object_filters is not None:
            raise DataSourceError('Filtering is not supported on S3JsonDataSource')
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')
        for entry in self.__raw_data:
            id_ = entry.get(self.id_attribute)
            if id_ is not None and id_ != '':
                yield self.__create_data_object(entry)