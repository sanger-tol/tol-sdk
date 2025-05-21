# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class StsManifestToElasticManifestConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = {f'sts_{k}': v for k, v in data_object.attributes.items()}
        attributes['sts_project'] = data_object.project.id \
            if data_object.project is not None else None
        attributes['sts_programme'] = data_object.project.programme \
            if data_object.project is not None else None
        attributes['sts_status'] = data_object.manifest_status.status \
            if data_object.manifest_status is not None else None
        attributes['sts_shipment_status'] = data_object.shipment_status.status \
            if data_object.shipment_status is not None else None
        attributes['sts_compliance_status'] = data_object.compliance_status.status \
            if data_object.compliance_status is not None else None

        # wildlife_compliance_processors
        wcp_attribute = []
        if data_object.wildlife_compliance_processors is not None:
            for wcp in data_object.wildlife_compliance_processors:
                wcp_attribute.append(wcp.user.fullname)
        attributes['sts_wildlife_compliance_processors'] = wcp_attribute

        ret = self._data_object_factory(
            'manifest',
            data_object.id,
            attributes=attributes
        )
        if data_object.sampleset is not None:
            ret.sts_sampleset = self._data_object_factory(
                'sampleset',
                data_object.sampleset.id
            )

        yield ret
