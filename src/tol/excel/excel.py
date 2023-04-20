# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pandas as pd


def convert_excel_to_json(file, sheet_name):
    excel_data = pd.read_excel(file, sheet_name=sheet_name)
    return excel_data.to_dict(orient='records')
