# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class StsSamplesetToElasticSamplesetConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = data_object.attributes
        attributes['gal_abbreviation'] = data_object.gal.abbreviation \
            if data_object.gal is not None else None
        attributes['project'] = data_object.project.id \
            if data_object.project is not None else None
        attributes['programme'] = data_object.project.programme \
            if data_object.project is not None else None
        attributes['status'] = data_object.sampleset_status.status \
            if data_object.sampleset_status is not None else None

        # SamplesetLegal is a one-to-many but we treat it as a one-to-one
        if data_object.sampleset_legals is not None:
            try:
                legal = next(data_object.sampleset_legals)
                attributes['legal_contract'] = legal.contract
                attributes['legal_reference'] = legal.reference
                attributes['legal_status'] = legal.status
                attributes['legal_comment'] = legal.comment
                attributes['legal_status_updated_at'] = \
                    legal.status_updated_at
            except StopIteration:
                pass

        # legal_compliance_processors
        lcp_attribute = []
        if data_object.legal_compliance_processors is not None:
            for lcp in data_object.legal_compliance_processors:
                lcp_attribute.append(lcp.user.fullname)
        attributes['legal_compliance_processors'] = lcp_attribute

        # sampleset_research_governance_processors
        rgp_attribute = []
        if data_object.sampleset_research_governance_processors is not None:
            for rgp in data_object.sampleset_research_governance_processors:
                rgp_attribute.append(rgp.user.fullname)
        attributes['research_governance_processors'] = rgp_attribute

        # sampleset_managers
        ssm_attribute = []
        if data_object.sampleset_managers is not None:
            for ssm in data_object.sampleset_managers:
                ssm_attribute.append(ssm.user.fullname)
        attributes['managers'] = ssm_attribute

        # There may be multiple SamplesetResearchGovernance each with different type
        if data_object.sampleset_research_governances is not None:
            for rg in data_object.sampleset_research_governances:
                research_governance_type = rg.research_governance_type.lower()
                attributes[f'rg_status_{research_governance_type}'] = \
                    rg.compliance_status.status if rg.compliance_status is not None else None
                attributes[f'rg_status_updated_at_{research_governance_type}'] = \
                    rg.updated_at
        ret = self._data_object_factory(
            'sampleset',
            data_object.id,
            attributes=attributes
        )
        yield ret
