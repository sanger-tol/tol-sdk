# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import tempfile
import uuid
import xml.etree.ElementTree as ElementTree
from typing import Dict, List, Tuple

sample_xml_template = """<?xml version="1.0" ?>
<SAMPLE_SET xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation=\
"ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.sample.xsd">
</SAMPLE_SET>"""


submission_xml_template = """<?xml version="1.0" encoding="UTF-8"?>
<SUBMISSION xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation=\
"ftp://ftp.sra.ebi.ac.uk/meta/xsd/sra_1_5/SRA.submission.xsd">
<CONTACTS></CONTACTS>
<ACTIONS>
<ACTION>
<ADD/>
</ACTION>
<ACTION>
<RELEASE/>
</ACTION>
</ACTIONS>
</SUBMISSION>"""


def convert_checklist_xml_to_dict(checklist_xml: str) -> Dict[str, Tuple[str, str, object]]:
    # key label, val [mandatory_status, ]

    fields = {}

    root = ElementTree.fromstring(checklist_xml)
    for field_group_node in root.findall('./CHECKLIST/DESCRIPTOR/FIELD_GROUP'):
        for field_node in field_group_node.findall('./FIELD'):

            label, mandatory_status = None, None

            label_node = field_node.find('./LABEL')

            if label_node is not None:
                label = label_node.text

            mandatory_node = field_node.find('./MANDATORY')

            if mandatory_node is not None:
                mandatory_status = mandatory_node.text

            regex_node = field_node.find('./FIELD_TYPE/TEXT_FIELD/REGEX_VALUE')
            if regex_node is not None:
                regex_str = regex_node.text
                fields[label] = [mandatory_status, 'restricted text', regex_str]
                continue

            text_choice_node = field_node.find('./FIELD_TYPE/TEXT_CHOICE_FIELD')

            if text_choice_node is not None:
                text_options = []
                for text_option_node in text_choice_node.findall('./TEXT_VALUE/VALUE'):
                    text_options.append(text_option_node.text)

                fields[label] = [mandatory_status, 'text choice', text_options]
                continue

            taxon_node = field_node.find('./FIELD_TYPE/TEXT_FIELD/TAXON_FIELD')

            if taxon_node is not None:
                regex_str = regex_node.text
                fields[label] = [mandatory_status, 'valid taxonomy', '']
                continue

            fields[label] = [mandatory_status, 'free text', '']

    return fields


def convert_xml_to_list_of_sample_dict(response_xml: str) -> List[Dict[str, List[str]]]:
    samples = []
    # Convert sample xml to dictionary
    # SAMPLE_ATTRIBUTE use TAG as key, tuple (VALUE, UNITS)
    # Additional entries TITLE, SAMPLE_NAME, TAXONID

    root = ElementTree.fromstring(response_xml)
    for xml_sample_node in root.findall('./SAMPLE'):
        sample = {}

        title, taxon_id, scientific_name = None, None, None

        title_node = xml_sample_node.find('./TITLE')
        taxon_id_node = xml_sample_node.find('./SAMPLE_NAME/TAXON_ID')
        scientific_name_node = xml_sample_node.find('./SAMPLE_NAME/SCIENTIFIC_NAME')

        if title_node is not None:
            title = title_node.text

        if taxon_id_node is not None:
            taxon_id = taxon_id_node.text

        if scientific_name_node is not None:
            scientific_name = scientific_name_node.text

        sample['title'] = [title, None]
        sample['taxon_id'] = [taxon_id, None]
        sample['scientific_name'] = [scientific_name, None]

        for xml_sample_attr_node in \
                xml_sample_node.findall('./SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE'):
            tag, val, units = None, None, None

            tag_node = xml_sample_attr_node.find('./TAG')
            val_node = xml_sample_attr_node.find('./VALUE')
            units_node = xml_sample_attr_node.find('./UNITS')

            if tag_node is not None:
                tag = tag_node.text

            if val_node is not None:
                val = val_node.text

            if units_node is not None:
                units = units_node.text

            sample[tag] = [val, units]

        samples.append(sample)

    return samples


def build_bundle_sample_xml(samples: Dict[str, Dict[str, List[str]]]) -> Tuple[str, int]:
    """build structure and save to file bundle_file_subfix.xml"""

    manifest_id = uuid.uuid4()

    dir_ = tempfile.TemporaryDirectory()

    filename = f'{dir_.name}bundle_{str(manifest_id)}.xml'

    with open(filename, 'w') as sample_xml_file:
        sample_xml_file.write(sample_xml_template)

    sample_count = update_bundle_sample_xml(samples, filename)

    return filename, sample_count


def update_bundle_sample_xml(samples: Dict[str, Dict[str, List[str]]], bundlefile: str) -> int:
    """update the sample with submission alias adding a new sample"""

    # print('adding sample to bundle sample xml')
    tree = ElementTree.parse(bundlefile)
    root = tree.getroot()
    sample_count = 0
    for title, sample in samples.items():
        sample_count += 1
        sample_alias = ElementTree.SubElement(root, 'SAMPLE')

        # Title is format <unique id>-<project name>-<specimen_type>
        t_arr = title.split('-')

        sample_alias.set('alias',
                         f'{t_arr[0]}-{t_arr[1]}-{t_arr[2]}-{t_arr[3]}-{t_arr[4]}')
        sample_alias.set('center_name', 'SangerInstitute')

        title_block = ElementTree.SubElement(sample_alias, 'TITLE')
        title_block.text = title
        sample_name = ElementTree.SubElement(sample_alias, 'SAMPLE_NAME')
        taxon_id = ElementTree.SubElement(sample_name, 'TAXON_ID')
        taxon_id.text = str(sample['taxon_id'][0])
        scientific_name = ElementTree.SubElement(sample_name, 'SCIENTIFIC_NAME')
        scientific_name.text = str(sample['scientific_name'][0])
        sample_attributes = ElementTree.SubElement(sample_alias, 'SAMPLE_ATTRIBUTES')

        for key, val in sample.items():

            if key in ['title', 'taxon_id', 'scientific_name']:
                continue

            sample_attribute = ElementTree.SubElement(sample_attributes, 'SAMPLE_ATTRIBUTE')
            tag = ElementTree.SubElement(sample_attribute, 'TAG')
            tag.text = key
            value = ElementTree.SubElement(sample_attribute, 'VALUE')
            value.text = str(val[0])
            # add ena units where necessary
            if val[1]:
                unit = ElementTree.SubElement(sample_attribute, 'UNITS')
                unit.text = val[1]

    ElementTree.dump(tree)
    tree.write(open(bundlefile, 'w'),
               encoding='unicode')
    return sample_count


def build_submission_xml(manifest_id: str, contact_name: str, contact_email: str) -> str:

    dir_ = tempfile.TemporaryDirectory()

    submissionfile = f'{dir_.name}submission_{str(manifest_id)}.xml'

    with open(submissionfile, 'w') as submission_xml_file:
        submission_xml_file.write(submission_xml_template)

    # build submission XML
    tree = ElementTree.parse(submissionfile)
    root = tree.getroot()

    # set SRA contacts
    contacts = root.find('CONTACTS')

    # set copo sra contacts
    copo_contact = ElementTree.SubElement(contacts, 'CONTACT')
    copo_contact.set('name', contact_name)
    copo_contact.set('inform_on_error', contact_email)
    copo_contact.set('inform_on_status', contact_email)
    ElementTree.dump(tree)

    tree.write(open(submissionfile, 'w'),
               encoding='unicode')

    return submissionfile


def assign_ena_ids(samples: str, xml: str) -> Dict[str, Dict[str, List[str]]]:

    try:
        tree = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return False

    success_status = tree.get('success')
    if success_status == 'false':
        return False
    else:
        return assign_biosample_accessions(samples, xml)


def assign_biosample_accessions(samples: Dict[str, Dict[str, List[str]]],
                                xml: str) -> Dict[str, Dict[str, List[str]]]:
    # Parse response to return generated biosample ids

    assigned_samples = {}

    tree = ElementTree.fromstring(xml)
    submission_accession = tree.find('SUBMISSION').get('accession')
    for child in tree.iter():
        if child.tag == 'SAMPLE':
            sample_id = child.get('alias')
            sra_accession = child.get('accession')
            biosample_accession = child.find('EXT_ID').get('accession')

            for key, sample_dict in samples.items():

                if sample_id in key:
                    sample_dict['sra_accession'] = [sra_accession, None]
                    sample_dict['biosample_accession'] = [biosample_accession, None]
                    sample_dict['submission_accession'] = [submission_accession, None]

                    assigned_samples[key] = sample_dict

    return assigned_samples
