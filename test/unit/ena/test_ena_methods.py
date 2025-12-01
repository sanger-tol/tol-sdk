# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.ena.ena_methods import (
    assign_ena_ids,
    build_bundle_sample_xml,
    build_submission_xml,
    convert_checklist_xml_to_dict,
    convert_xml_to_list_of_sample_dict,
)


class TestENAMethods(TestCase):

    def test_convert_checklist_xml_to_dict(self):

        checklist_xml = """<?xml version="1.0" encoding="UTF-8"?>
<CHECKLIST_SET>
<CHECKLIST accession="ERC000053" checklistType="Sample">
          <IDENTIFIERS>
               <PRIMARY_ID>ERC000053</PRIMARY_ID>
          </IDENTIFIERS>
          <DESCRIPTOR>
               <LABEL>Tree of Life Checklist</LABEL>
               <NAME>Tree of Life Checklist</NAME>
               <DESCRIPTION>Minimum information required for reporting samples associated with \
 the Tree of Life Programme (https://www.sanger.ac.uk/programme/tree-of-life/).</DESCRIPTION>
               <AUTHORITY>ENA</AUTHORITY>
               <FIELD_GROUP restrictionType="Any number or none of the fields">
                    <NAME>Part and developmental stage of organism</NAME>
                    <DESCRIPTION>Anatomical and developmental descriptions of the sample site \
or source material</DESCRIPTION>
                    <FIELD>
                         <LABEL>organism part</LABEL>
                         <NAME>organism part</NAME>
                         <DESCRIPTION>The part of organism's anatomy or substance arising from \
an organism from which the biomaterial was derived, excludes cells.</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_FIELD/>
                         </FIELD_TYPE>
                         <MANDATORY>mandatory</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
               </FIELD_GROUP>
               <FIELD_GROUP restrictionType="Any number or none of the fields">
                    <NAME>non-sample terms</NAME>
                    <FIELD>
                         <LABEL>project name</LABEL>
                         <NAME>project name</NAME>
                         <DESCRIPTION>Name of the project within which the sequencing was \
organized</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_FIELD/>
                         </FIELD_TYPE>
                         <MANDATORY>mandatory</MANDATORY>
                         <MULTIPLICITY>multiple</MULTIPLICITY>
                    </FIELD>
               </FIELD_GROUP>
               <FIELD_GROUP restrictionType="Any number or none of the fields">
                    <NAME>Collection event information</NAME>
                    <FIELD>
                         <LABEL>collected_by</LABEL>
                         <NAME>collected_by</NAME>
                         <DESCRIPTION>name of persons or institute who collected the \
specimen</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_AREA_FIELD/>
                         </FIELD_TYPE>
                         <MANDATORY>mandatory</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
                    <FIELD>
                         <LABEL>collection date</LABEL>
                         <NAME>collection date</NAME>
                         <DESCRIPTION>The date of sampling, either as an instance \
(single point in time) or interval. In case no exact time is available, the date/time can \
be right truncated i.e. all of these are valid ISO8601 compliant times: \
2008-01-23T19:23:10+00:00; 2008-01-23T19:23:10; 2008-01-23; 2008-01; 2008.</DESCRIPTION> \
                         <FIELD_TYPE>
                              <TEXT_FIELD>
                                   <REGEX_VALUE>\
(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-]\
[0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]\
{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)</REGEX_VALUE>
                              </TEXT_FIELD>
                         </FIELD_TYPE>
                         <MANDATORY>mandatory</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
               </FIELD_GROUP>
               <FIELD_GROUP restrictionType="Any number or none of the fields">
                    <NAME>Organism characteristics</NAME>
                    <DESCRIPTION>Characteristics of the source organism</DESCRIPTION>
                    <FIELD>
                         <LABEL>sex</LABEL>
                         <NAME>sex</NAME>
                         <DESCRIPTION>sex of the organism from which the sample \
was obtained</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_FIELD/>
                         </FIELD_TYPE>
                         <MANDATORY>mandatory</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
                    <FIELD>
                         <LABEL>relationship</LABEL>
                         <NAME>relationship</NAME>
                         <DESCRIPTION>indicates if the specimen has a known relationship to \
another specimen (e.g. parental, child, sibling or other kind of relationship)</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_FIELD/>
                         </FIELD_TYPE>
                         <MANDATORY>optional</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
                    <FIELD>
                         <LABEL>symbiont</LABEL>
                         <NAME>symbiont</NAME>
                         <DESCRIPTION>Used to separate host and symbiont metadata within a \
symbiont system where the host species are indicated as 'N' and symbionts are indicated \
as 'Y'</DESCRIPTION>
                         <FIELD_TYPE>
                              <TEXT_CHOICE_FIELD>
                                   <TEXT_VALUE>
                                        <VALUE>N</VALUE>
                                   </TEXT_VALUE>
                                   <TEXT_VALUE>
                                        <VALUE>Y</VALUE>
                                   </TEXT_VALUE>
                              </TEXT_CHOICE_FIELD>
                         </FIELD_TYPE>
                         <MANDATORY>optional</MANDATORY>
                         <MULTIPLICITY>single</MULTIPLICITY>
                    </FIELD>
               </FIELD_GROUP>
          </DESCRIPTOR>
     </CHECKLIST>
</CHECKLIST_SET>
"""

        expected = [{
            'checklist_id': 'ERC000053',
            'checklist': {
                'organism part': ['mandatory', 'free text', ''],
                'project name': ['mandatory', 'free text', ''],
                'collected_by': ['mandatory', 'free text', ''],
                'collection date': [
                    'mandatory',
                    'restricted text',
                    '(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]'
                    '{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}'
                    '(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)'
                    '|(^not collected$)|(^not provided$)|(^restricted access$)'
                ],
                'sex': ['mandatory', 'free text', ''],
                'relationship': ['optional', 'free text', ''],
                'symbiont': ['optional', 'text choice', ['N', 'Y']]
            }
        }]
        self.assertEqual(expected, convert_checklist_xml_to_dict(checklist_xml))

    def test_convert_xml_to_list_of_sample_dict(self):

        response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<SAMPLE_SET>
<SAMPLE accession="SAMEA1234567" alias="CollectionInstituteID" center_name="CollectionInstitute" \
broker_name="CollectionInstitute account">
     <IDENTIFIERS>
          <PRIMARY_ID>SAMEA1234567</PRIMARY_ID>
          <SECONDARY_ID>ERS1234567</SECONDARY_ID>
          <EXTERNAL_ID namespace="BioSample">SAMEA1234567</EXTERNAL_ID>
          <SUBMITTER_ID namespace="CollectionInstitute">CollectionInstituteID</SUBMITTER_ID>
     </IDENTIFIERS>
     <TITLE>uniqueid-first-second-third-fourth-TEST-specimen</TITLE>
     <SAMPLE_NAME>
          <TAXON_ID>9606</TAXON_ID>
          <SCIENTIFIC_NAME>Homo sapiens</SCIENTIFIC_NAME>
     </SAMPLE_NAME>
     <SAMPLE_LINKS>
    <SAMPLE_LINK>
        <XREF_LINK>
            <DB>ENA-FASTQ-FILES</DB>
            <ID><![CDATA[https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERS6264840 \
&result=read_run&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes]]></ID>
        </XREF_LINK>
    </SAMPLE_LINK>
    <SAMPLE_LINK>
        <XREF_LINK>
            <DB>ENA-SUBMITTED-FILES</DB>
            <ID><![CDATA[https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERS6264840 \
&result=read_run&fields=run_accession,submitted_ftp,submitted_md5, \
submitted_bytes,submitted_format]]></ID>
        </XREF_LINK>
    </SAMPLE_LINK>
</SAMPLE_LINKS>
<SAMPLE_ATTRIBUTES>
          <SAMPLE_ATTRIBUTE>
               <TAG>geographic location (depth)</TAG>
               <VALUE>0.01</VALUE>
               <UNITS>m</UNITS>
          </SAMPLE_ATTRIBUTE>
          <SAMPLE_ATTRIBUTE>
               <TAG>organism part</TAG>
               <VALUE>WHOLE ORGANISM</VALUE>
          </SAMPLE_ATTRIBUTE>
          <SAMPLE_ATTRIBUTE>
               <TAG>ENA-LAST-UPDATE</TAG>
               <VALUE>2021-04-19</VALUE>
          </SAMPLE_ATTRIBUTE>
     </SAMPLE_ATTRIBUTES>
</SAMPLE>
</SAMPLE_SET>
        """

        expected = [
            {
                'title': ['uniqueid-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': ['9606', None],
                'scientific_name': ['Homo sapiens', None],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None]
            }
        ]

        self.assertEqual(expected, convert_xml_to_list_of_sample_dict(response_xml))

    def test_build_bundle_sample_xml(self):

        samples = {
            'uniqueidone-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidone-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': ['9606', None],
                'scientific_name': ['Homo sapiens', None],
                'completeness score': [79.23, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None]
            },
            'uniqueidtwo-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidtwo-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': [8961, None],
                'scientific_name': ['Aquila audax', None],
                'completeness score': [89.44, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None]
            }
        }

        expected_xml = """<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xsi:noNamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.sample.xsd">
<SAMPLE alias="uniqueidone-first-second-third-fourth" center_name="SangerInstitute">\
<TITLE>uniqueidone-first-second-third-fourth-TEST-specimen</TITLE><SAMPLE_NAME><TAXON_ID>9606\
</TAXON_ID><SCIENTIFIC_NAME>Homo sapiens</SCIENTIFIC_NAME></SAMPLE_NAME><SAMPLE_ATTRIBUTES>\
<SAMPLE_ATTRIBUTE><TAG>completeness score</TAG><VALUE>79.23</VALUE><UNITS>%</UNITS>\
</SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>geographic location (depth)</TAG><VALUE>0.01</VALUE>\
<UNITS>m</UNITS></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>organism part</TAG>\
<VALUE>WHOLE ORGANISM</VALUE></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>ENA-LAST-UPDATE</TAG>\
<VALUE>2021-04-19</VALUE></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>sample derived from</TAG>\
<VALUE>SAMEA123456789</VALUE></SAMPLE_ATTRIBUTE></SAMPLE_ATTRIBUTES></SAMPLE>\
<SAMPLE alias="uniqueidtwo-first-second-third-fourth" center_name="SangerInstitute">\
<TITLE>uniqueidtwo-first-second-third-fourth-TEST-specimen</TITLE><SAMPLE_NAME><TAXON_ID>8961\
</TAXON_ID><SCIENTIFIC_NAME>Aquila audax</SCIENTIFIC_NAME></SAMPLE_NAME><SAMPLE_ATTRIBUTES>\
<SAMPLE_ATTRIBUTE><TAG>completeness score</TAG><VALUE>89.44</VALUE><UNITS>%</UNITS>\
</SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>geographic location (depth)</TAG><VALUE>0.01\
</VALUE><UNITS>m</UNITS></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>organism part</TAG><VALUE>\
WHOLE ORGANISM</VALUE></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>ENA-LAST-UPDATE</TAG><VALUE>\
2021-04-19</VALUE></SAMPLE_ATTRIBUTE><SAMPLE_ATTRIBUTE><TAG>sample derived from</TAG><VALUE>\
SAMEA123456789</VALUE></SAMPLE_ATTRIBUTE></SAMPLE_ATTRIBUTES></SAMPLE></SAMPLE_SET>"""

        bundle_xml_file, sample_count = build_bundle_sample_xml(samples)

        with open(bundle_xml_file, 'r') as bxf:
            bundle_xml_file_contents = bxf.read()

        self.assertEqual(expected_xml, bundle_xml_file_contents)
        self.assertEqual(len(samples), sample_count)

    def test_build_submission_xml(self):

        expected_xml = """<SUBMISSION xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
 xsi:noNamespaceSchemaLocation="ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.submission.xsd">
<CONTACTS><CONTACT name="Sanger Tree of Life Enabling Platforms Team" inform_on_error=\
"tol-platforms@sanger.ac.uk" inform_on_status="tol-platforms@sanger.ac.uk" /></CONTACTS>
<ACTIONS>
<ACTION>
<ADD />
</ACTION>
<ACTION>
<RELEASE />
</ACTION>
</ACTIONS>
</SUBMISSION>"""

        manifest_id = 'unique_manifest_id'
        contact_name = 'Sanger Tree of Life Enabling Platforms Team'
        contact_email = 'tol-platforms@sanger.ac.uk'

        submission_xml_file = build_submission_xml(manifest_id, contact_name, contact_email)

        with open(submission_xml_file, 'r') as sxf:
            submission_xml_file_contents = sxf.read()

        self.assertEqual(expected_xml, submission_xml_file_contents)
        self.assertIn(f'submission_{str(manifest_id)}.xml', submission_xml_file)

    def test_assign_ena_ids(self):

        samples = {
            'uniqueidone-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidone-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': ['9606', None],
                'scientific_name': ['Homo sapiens', None],
                'completeness score': [79.23, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None]
            },
            'uniqueidtwo-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidtwo-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': [8961, None],
                'scientific_name': ['Aquila audax', None],
                'completeness score': [89.44, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None]
            }
        }
        submission_response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="receipt.xsl"?>
<RECEIPT receiptDate="2023-04-03T16:39:10.614+01:00" \
submissionFile="tmp11faxkwjsubmission_unique_manifest_id.xml" success="true">
     <SAMPLE accession="ERS12345670" alias="uniqueidone-first-second-third-fourth" status="PUBLIC">
          <EXT_ID accession="SAMEA123456780" type="biosample"/>
     </SAMPLE>
     <SAMPLE accession="ERS12345671" alias="uniqueidtwo-first-second-third-fourth" status="PUBLIC">
          <EXT_ID accession="SAMEA123456781" type="biosample"/>
     </SAMPLE>
     <SUBMISSION accession="ERA12345678" alias="SUBMISSION-03-04-2023-16:39:10:198"/>
     <MESSAGES>
          <INFO>All objects in this submission are set to public status (RELEASE).</INFO>
          <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
     </MESSAGES>
     <ACTIONS>ADD</ACTIONS>
     <ACTIONS>RELEASE</ACTIONS>
</RECEIPT>
"""

        expected_samples = {
            'uniqueidone-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidone-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': ['9606', None],
                'scientific_name': ['Homo sapiens', None],
                'completeness score': [79.23, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None],
                'sra_accession': ['ERS12345670', None],
                'biosample_accession': ['SAMEA123456780', None],
                'submission_accession': ['ERA12345678', None],
            },
            'uniqueidtwo-first-second-third-fourth-TEST-specimen': {
                'title': ['uniqueidtwo-first-second-third-fourth-TEST-specimen', None],
                'taxon_id': [8961, None],
                'scientific_name': ['Aquila audax', None],
                'completeness score': [89.44, '%'],
                'geographic location (depth)': ['0.01', 'm'],
                'organism part': ['WHOLE ORGANISM', None],
                'ENA-LAST-UPDATE': ['2021-04-19', None],
                'sample derived from': ['SAMEA123456789', None],
                'sra_accession': ['ERS12345671', None],
                'biosample_accession': ['SAMEA123456781', None],
                'submission_accession': ['ERA12345678', None],
            }
        }

        self.assertEqual(expected_samples, assign_ena_ids(samples, submission_response_xml))
