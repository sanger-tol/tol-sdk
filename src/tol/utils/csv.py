# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import numpy as np

import pandas as pd


def convert_csv_to_json(file_path, sep=',', usecols=None):
    csv_file = pd.read_csv(
        file_path,
        sep=sep,
        header=0,
        index_col=False,
        usecols=usecols
    )
    csv_file.replace({np.nan: None}, inplace=True)
    return csv_file.to_dict(orient='records')
