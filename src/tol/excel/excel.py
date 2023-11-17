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


def convert_data_objects_to_excel(data_objects, body, sheet_name):
    # Create a binary stream to where Excel data will be written to
    output_stream = io.BytesIO()
    writer = pd.ExcelWriter(output_stream, engine='xlsxwriter')

    # Extract the visible columns and their order for the excel column headers
    column_order = [field['dataField'] for field in body if not field['hidden']]
    df = pd.DataFrame(columns=column_order)

    for data_object in data_objects:
        data = {}

        # Find the data object attribute matching the column name and extract the value
        for column in column_order:
            attr_value = data_object.attributes.get(column, '')
            if not attr_value and column in data_object.to_one_relationships:
                attr_value = data_object.to_one_relationships[column].id

            data[column] = attr_value

        # Append to data frame
        df = df.append(data, ignore_index=True)

    # Convert the data frame to Excel
    df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
    writer.save()
    writer.close()

    return output_stream
