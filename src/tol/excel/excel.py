# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import io

import numpy as np

import pandas as pd


def convert_excel_to_json(file, sheet_name):
    excel_data = pd.read_excel(file, sheet_name=sheet_name)
    excel_data.replace({np.nan: None}, inplace=True)
    return excel_data.to_dict(orient='records')


def convert_excel_to_valid_json_string(file, sheet_name) -> str:
    """Converts all (date)times to strings"""

    excel_data = pd.read_excel(file, sheet_name=sheet_name)
    excel_data.replace({np.nan: None}, inplace=True)
    return excel_data.to_json(orient='records', date_format='iso')


def convert_data_objects_to_excel(data_objects, body, sheet_name):
    # Create a binary stream to where Excel data will be written to
    output_stream = io.BytesIO()
    writer = pd.ExcelWriter(output_stream, engine='xlsxwriter')

    # Extract the visible columns and their order for the excel column headers
    column_order = [field['display_name'] for field in body if not field['hidden']]
    df = pd.DataFrame(columns=column_order)

    for data_object in data_objects:
        data = {}

        for field in body:
            if not field['hidden']:
                display_name = field['display_name']
                key = field['key']

                if '.' in key:
                    relationship, relationship_attribute = key.split('.')
                else:
                    relationship, relationship_attribute = None, None

                attr_value = ''

                if key in data_object.attributes:
                    attr_value = data_object.attributes.get(key, '')
                elif (data_object.to_one_relationships is not None
                      and relationship in data_object.to_one_relationships):
                    to_one_relationship = data_object.to_one_relationships[relationship]
                    attr_value = getattr(to_one_relationship, relationship_attribute)

                data[display_name] = attr_value

        # Append to data frame
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)

    # Convert the data frame to Excel
    df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
    writer.close()

    return output_stream
